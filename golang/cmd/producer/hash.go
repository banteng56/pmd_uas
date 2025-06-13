package producer

import (
    "crypto/sha256"
    "encoding/hex"
)

func GenerateHash(input string) string {
    hash := sha256.New()
    hash.Write([]byte(input))
    return hex.EncodeToString(hash.Sum(nil))
}
