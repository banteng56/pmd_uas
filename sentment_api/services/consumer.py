import json
import asyncio
import logging
from datetime import datetime
from typing import Optional
import aio_pika
from aio_pika.abc import AbstractIncomingMessage
from core.config import settings
from services.text_cleaner import TextCleaner
from services.database import DatabaseService

logger = logging.getLogger(__name__)

class RabbitMQConsumer:
    def __init__(self, model_trainer):
        self.model_trainer = model_trainer
        self.text_cleaner = TextCleaner()
        self.db_service = DatabaseService()
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.processed_count = 0
        self.error_count = 0
        self.running = False
    
    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            self.channel = await self.connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"RabbitMQ connection failed: {e}")
            raise
    
    async def start_consuming(self):
        if not self.model_trainer.training_completed:
            logger.info("Waiting for models to complete training")
            while not self.model_trainer.training_completed:
                await asyncio.sleep(1)
        
        await self.connect()
        await self.db_service.connect()
        
        try:
            queue = await self.channel.declare_queue(
                settings.QUEUE_NAME,
                durable=True
            )
            
            logger.info(f"Started consuming from queue: {settings.QUEUE_NAME}")
            self.running = True
            
            await queue.consume(self.process_message)
            
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            self.running = False
        finally:
            if self.connection:
                await self.connection.close()
            await self.db_service.close()
    
    async def process_message(self, message: AbstractIncomingMessage):
        try:
            body = message.body.decode('utf-8')
            data = json.loads(body)
            
            url = data.get('url', '')
            content = data.get('content', '')
            
            if not url or not content:
                logger.warning(f"Invalid message format: {data}")
                await message.ack()
                return
            
            logger.info(f"Processing article: {url}")
            
            cleaned_content = self.text_cleaner.clean(content)
            
            if not cleaned_content.strip():
                logger.warning(f"No content after cleaning: {url}")
                await message.ack()
                return
            
            predictions = self.model_trainer.predict_sentiment(cleaned_content)
            
            await self.db_service.save_prediction(
                url=url,
                content=cleaned_content,
                mlp_label=predictions['mlp']['encoded'],
                hmm_label=predictions['hmm']['encoded']
            )
            
            result = {
                "url": url,
                "predictions": predictions,
                "processed_at": datetime.now().isoformat()
            }
            
            logger.info(f"Processed: {url}")
            logger.info(f"MLP: {predictions['mlp']['sentiment']} ({predictions['mlp']['encoded']})")
            logger.info(f"HMM: {predictions['hmm']['sentiment']} ({predictions['hmm']['encoded']})")
            
            self.processed_count += 1
            await message.ack()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.error_count += 1
            await message.nack(requeue=False)
    
    async def stop(self):
        logger.info("Stopping consumer")
        self.running = False
        if self.connection:
            await self.connection.close()
        await self.db_service.close()
    
    def get_stats(self):
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "running": self.running
        }