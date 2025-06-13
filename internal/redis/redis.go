package redis

import (
    "context"
    "github.com/go-redis/redis/v8"
    "log"
    "time"
)

var rdb *redis.Client

func InitRedis() {
    rdb = redis.NewClient(&redis.Options{
        Addr:     "localhost:6379", 
        Password: "",          
        DB:       0,               
    })

    _, err := rdb.Ping(context.Background()).Result()
    if err != nil {
        log.Fatal("Failed to connect to Redis:", err)
    }
    log.Println("Connected to Redis.")
}

func CheckAndSetHash(ctx context.Context, hash string) bool {
    exists, err := rdb.Exists(ctx, hash).Result()
    if err != nil {
        log.Fatal("Error checking hash in Redis:", err)
    }
    if exists > 0 {
        return false 
    }

    err = rdb.SetEX(ctx, hash, "exists", 24*time.Hour).Err()
    if err != nil {
        log.Fatal("Error setting hash in Redis:", err)
    }
    return true
}
func SaveToCache(url, content string) error {
    ctx := context.Background()
    err := rdb.Set(ctx, url, content, 24*time.Hour).Err()
    if err != nil {
        log.Println("Failed to save to Redis:", err)
    }
    return err
}