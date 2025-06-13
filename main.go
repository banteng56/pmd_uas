package main

import (
	"context"
	"log"
	"sync"
	"time"
	"github.com/streadway/amqp"
	"tugaspmd/cmd/producer"
	"tugaspmd/cmd/consumer"
	"tugaspmd/internal/redis"
	"tugaspmd/internal/postgres"
)

func main() {
	redis.InitRedis()

	pgConn, err := postgres.InitDB()
	if err != nil {
		log.Fatal("Failed to connect to PostgreSQL:", err)
	}
	defer pgConn.Close(context.Background())

	chProducer, connProducer, err := producer.InitRabbitMQ()
	if err != nil {
		log.Fatal("Failed to initialize RabbitMQ for Producer: ", err)
	}
	defer connProducer.Close()
	defer chProducer.Close()

	connConsumer, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	if err != nil {
		log.Fatal("Failed to connect to RabbitMQ for Consumer:", err)
	}
	defer connConsumer.Close()

	chConsumer, err := connConsumer.Channel()
	if err != nil {
		log.Fatal("Failed to open a channel for Consumer:", err)
	}
	defer chConsumer.Close()

	feeds := []string{
		"https://news.detik.com/berita/rss",
		"https://finance.detik.com/rss",
		"https://rss.tempo.co/nasional",
		"https://rss.tempo.co/bisnis",	}

	var wg sync.WaitGroup

	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Println("Producer started.")
		for {
			for _, feedURL := range feeds {
				items, err := producer.FetchRSS(feedURL)
				if err != nil {
					log.Printf("Failed to fetch RSS feed from %s: %v", feedURL, err)
					continue
				}

				for _, item := range items {
					hash := producer.GenerateHash(item.Link)

					ctx := context.Background()
					if !redis.CheckAndSetHash(ctx, hash) {
						log.Printf("Duplicate found for %s, skipping", item.Link)
						continue
					}

					imageURL := ""
					if item.Image != nil {
						imageURL = item.Image.URL
					}
					err := postgres.SaveArticleMetadata(pgConn, item.Title, item.Link, item.Published, imageURL)			
					if err != nil {
						log.Printf("Failed to save metadata to PostgreSQL: %v", err)
					} else {
						log.Printf("Saved metadata for: %s", item.Title)
					}

					err = producer.SendToQueue(chProducer, item.Link, "rss-feed")
					if err != nil {
						log.Printf("Failed to send message to RabbitMQ (rss-feed): %v", err)
						continue
					}

					log.Printf("Successfully processed article: %s", item.Title)
				}
			}
			time.Sleep(5 * time.Minute)
		} 
	}()

	wg.Add(1)
	go func() {
		defer wg.Done()
		log.Println("Consumer started.")
		numConsumers := 5 

		for i := 0; i < numConsumers; i++ {
			go func(consumerID int) {
				chConsumer, connConsumer, err := checkAndReconnect(chConsumer, connConsumer)
				if err != nil {
					log.Fatalf("Failed to reconnect RabbitMQ: %v", err)
				}
				defer connConsumer.Close()
				defer chConsumer.Close()

				msgs, err := chConsumer.Consume(
					"rss-feed",
					"",
					false, 
					false,
					false,
					false,
					nil,
				)
				if err != nil {
					log.Fatal("Failed to register a consumer:", err)
				}

				for msg := range msgs {
					log.Printf("Consumer %d received message: %s\n", consumerID, string(msg.Body))
					consumer.ProcessMessage(chConsumer, msg)
					err := msg.Ack(false)
					if err != nil {
						log.Printf("Error acknowledging message: %v", err)
					}
				}
			}(i)
		}
	}()

	wg.Wait()
}

func checkAndReconnect(ch *amqp.Channel, conn *amqp.Connection) (*amqp.Channel, *amqp.Connection, error) {
	if conn.IsClosed() {
		var err error
		conn, err = amqp.Dial("amqp://guest:guest@localhost:5672/")
		if err != nil {
			return nil, nil, err
		}

		ch, err = conn.Channel()
		if err != nil {
			return nil, nil, err
		}
	}
	return ch, conn, nil
}