package postgres

import (
	"context"
	"log"
	"time"
	"github.com/jackc/pgx/v4"
	"strings"
)

func getCurrentTimestamp() string {
	return time.Now().Format(time.RFC3339)
}

func InitDB() (*pgx.Conn, error) {
	conn, err := pgx.Connect(context.Background(), "postgres://postgres:password@localhost:5432/pmd")
	if err != nil {
		return nil, err
	}
	return conn, nil
}

func SaveToDB(url, content string) error {
    conn, err := InitDB()
    if err != nil {
        return err
    }
    defer conn.Close(context.Background())

    wordCount := len(strings.Fields(content))
    priority := 1 
    if wordCount >= 300 {
        priority = 2
    }

    var markValue string
    var lastProcessedTime string
    if content == "" {
        content = "No content available"
        markValue = "incomplete"
        priority = 0 
        lastProcessedTime = getCurrentTimestamp() 
    } else {
        markValue = "complete"
        lastProcessedTime = getCurrentTimestamp() 
    }

    query := `UPDATE articles 
              SET content = $1, 
                  mark = $2,
                  priority = $3,
                  last_processed_time = $4
              WHERE url = $5`
    
    _, err = conn.Exec(
        context.Background(),
        query,
        content,
        markValue,
        priority,
        lastProcessedTime, 
        url,
    )
    
    if err != nil {
        log.Printf("Failed to update article: %v", err)
        return err
    }
    return nil
}


func SaveArticleMetadata(conn *pgx.Conn, title, url, published, imageURL string) error {
    markValue := "incomplete" 
    lastProcessedTime := getCurrentTimestamp() 
    statusValue := "process" 

    query := `INSERT INTO articles (title, url, published_at, mark, content, last_processed_time, status, img)
            VALUES ($1, $2, $3::timestamp, $4, NULL, $5::timestamp, $6, $7)
            ON CONFLICT (url) DO UPDATE 
            SET title = EXCLUDED.title,
                published_at = EXCLUDED.published_at,
                mark = $4,
                last_processed_time = $5::timestamp,
                status = $6,
                img = EXCLUDED.img`
        _, err := conn.Exec(
            context.Background(),
            query,
            title, url, published, markValue, lastProcessedTime, statusValue, imageURL,
        )
    
    if err != nil {
        log.Printf("Failed to save metadata to PostgreSQL: %v", err)
        return err
    }
    return nil
}


