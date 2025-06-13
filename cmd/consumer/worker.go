package consumer

import (
    "fmt"
    "tugaspmd/cmd/consumer/extractor"
    "tugaspmd/internal/postgres"
    "github.com/streadway/amqp"
    "strings"
    "tugaspmd/cmd/producer"

)

func ProcessMessage(ch *amqp.Channel, msg amqp.Delivery) {
    articleURL := string(msg.Body)
    fmt.Printf("Processing article: %s\n", articleURL)

    var content string
    var err error

    switch {
    case contains(articleURL, "detik.com"):
        content, err = extractor.ExtractDetik(articleURL)
    case contains(articleURL, "tempo.co"):
        content, err = extractor.ExtractTempo(articleURL)
    default:
        fmt.Println("Unsupported source:", articleURL)
        return
    }

    if err != nil {
        fmt.Printf("Error extracting content for %s: %v\n", articleURL, err)
        return
    }

    err = postgres.SaveToDB(articleURL, content)
    if err != nil {
        fmt.Println("Error saving to PostgreSQL:", err)
    }
    err = producer.SendCleanToQueue(ch, articleURL, content)
    if err != nil {
        fmt.Println("Gagal mengirim ke antrian rss-clean:", err)
    }
}

func contains(url, keyword string) bool {
    return strings.Contains(url, keyword)
}
