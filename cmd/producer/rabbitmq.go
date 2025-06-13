package producer

import (
	"log"
	"github.com/streadway/amqp"
	"sync"
	"encoding/json"

)

func InitRabbitMQ() (*amqp.Channel, *amqp.Connection, error) {
	conn, err := amqp.Dial("amqp://guest:guest@localhost:5672/")
	if err != nil {
		return nil, nil, err
	}

	ch, err := conn.Channel()
	if err != nil {
		return nil, nil, err	
	}

	err = ch.Qos(1, 0, false)  
	if err != nil {
		return nil, nil, err
	}

	_, err = ch.QueueDeclare(
		"rss-feed", 
		true,        
		false,      
		false,        
		false,      
		nil,        
	)
	if err != nil {
		log.Fatalf("Failed to declare queue: %v", err)
	}

	return ch, conn, nil
}

func processMessage(msg string) {
	log.Printf("Processing message: %s\n", msg)
}

func startMultipleConsumers(ch *amqp.Channel, numConsumers int) {
	var wg sync.WaitGroup

	for i := 0; i < numConsumers; i++ {
		wg.Add(1)
		go func(workerID int) {
			defer wg.Done()

			msgs, err := ch.Consume(
				"rss-feed", 
				"",        
				true,       
				false,   
				false,   
				false,    
				nil,       
			)
			if err != nil {
				log.Fatalf("Failed to register a consumer: %v", err)
			}

			for msg := range msgs {
				log.Printf("Worker %d received message: %s\n", workerID, msg.Body)
				processMessage(string(msg.Body))
			}
		}(i)
	}

	wg.Wait()
}

func SendToQueue(ch *amqp.Channel, message string, routingKey string) error {
	err := ch.Publish(
		"",          
		routingKey,   
		false,     
		false,      
		amqp.Publishing{
			ContentType: "text/plain",
			Body:        []byte(message),
		})
	return err
}
type CleanMessage struct {
    URL     string `json:"url"`
    Content string `json:"content"`
}

func SendCleanToQueue(ch *amqp.Channel, url string, content string) error {
    body, err := json.Marshal(CleanMessage{
        URL:     url,
        Content: content,
    })
    if err != nil {
        return err
    }

    return ch.Publish(
        "",
        "rss-clean",
        false,
        false,
        amqp.Publishing{
            ContentType: "application/json",
            Body:        body,
        },
    )
}
