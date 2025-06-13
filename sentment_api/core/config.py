import os

class Settings:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    RABBITMQ_URL: str = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    QUEUE_NAME: str = "rss-clean"
    
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgres://postgres:password@localhost:5432/pmd")
    
    MAX_FEATURES: int = 5000
    MLP_HIDDEN_SIZE: int = 128
    MLP_EPOCHS: int = 50
    MLP_LEARNING_RATE: float = 0.01
    HMM_MAX_ITER: int = 10

settings = Settings()