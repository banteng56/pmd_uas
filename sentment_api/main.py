import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from models.train_models import ModelTrainer
from services.consumer import RabbitMQConsumer
from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

model_trainer = None
consumer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model_trainer, consumer
    
    logger.info("Starting application")
    
    logger.info("Training models")
    model_trainer = ModelTrainer()
    await model_trainer.train_all_models()
    logger.info("Models training completed")
    
    logger.info("Starting RabbitMQ consumer")
    consumer = RabbitMQConsumer(model_trainer)
    consumer_task = asyncio.create_task(consumer.start_consuming())
    logger.info("Consumer started")
    
    app.state.model_trainer = model_trainer
    app.state.consumer = consumer
    
    logger.info("Application ready")
    
    yield
    
    logger.info("Shutting down")
    if consumer:
        await consumer.stop()
    consumer_task.cancel()

app = FastAPI(
    title="Sentiment Analysis Consumer",
    description="FastAPI app that consumes RSS articles and predicts sentiment using MLP and HMM models",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Sentiment Analysis Consumer API",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )