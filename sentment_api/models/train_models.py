import numpy as np
import asyncio
import logging
from datasets import load_dataset
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import LabelEncoder
from .hmm_model import HMM
from .mlp_model import MLP
from core.config import settings

logger = logging.getLogger(__name__)

class ModelTrainer:
    def __init__(self):
        self.mlp_model = None
        self.hmm_model = None
        self.vectorizer = None
        self.label_encoder = None
        self.mlp_accuracy = 0.0
        self.hmm_accuracy = 0.0
        self.training_completed = False
    
    async def train_all_models(self):
        try:
            logger.info("Loading datasets")
            X_train, X_test, y_train, y_test = await self._load_and_prepare_data()
            
            logger.info("Training MLP model")
            await self._train_mlp(X_train, X_test, y_train, y_test)
            
            logger.info("Training HMM model")
            await self._train_hmm(X_train, X_test, y_train, y_test)
            
            self.training_completed = True
            logger.info(f"Training completed - MLP: {self.mlp_accuracy:.4f}, HMM: {self.hmm_accuracy:.4f}")
            
        except Exception as e:
            logger.error(f"Training error: {e}")
            raise
    
    async def _load_and_prepare_data(self):
        ds_sepid = load_dataset("sepidmnorozy/Indonesian_sentiment")
        data_sepid = ds_sepid['train']
        
        ds_indonlu = load_dataset("indonlu", "smsa", trust_remote_code=True)
        data_indonlu = ds_indonlu['train']
        
        label_names = data_indonlu.features["label"].names
        neutral_label_id = label_names.index("neutral")
        neutral_data = [item for item in data_indonlu if item["label"] == neutral_label_id]
        
        texts = data_sepid['text'] + [item['text'] for item in neutral_data]
        labels = data_sepid['label'] + ["neutral" for _ in neutral_data]
        
        self.label_encoder = LabelEncoder()
        y = self.label_encoder.fit_transform(labels)
        
        self.vectorizer = CountVectorizer(max_features=settings.MAX_FEATURES, stop_words=None)
        X = self.vectorizer.fit_transform(texts).toarray()
        print('udah disini')
        print(X.shape)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Data prepared: {X_train.shape[0]} train, {X_test.shape[0]} test samples")
        return X_train, X_test, y_train, y_test
    
    async def _train_mlp(self, X_train, X_test, y_train, y_test):
        input_size = X_train.shape[1]
        output_size = len(np.unique(y_train))
        
        self.mlp_model = MLP(
            input_size=input_size,
            hidden_size=settings.MLP_HIDDEN_SIZE,
            output_size=output_size,
            learning_rate=settings.MLP_LEARNING_RATE
        )
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, 
            self.mlp_model.train, 
            X_train, y_train, settings.MLP_EPOCHS, 32
        )
        
        y_pred = self.mlp_model.predict(X_test)
        self.mlp_accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"MLP accuracy: {self.mlp_accuracy:.4f}")
    
    async def _train_hmm(self, X_train, X_test, y_train, y_test):
        n_states = len(np.unique(y_train))
        n_emissions = X_train.shape[1]
        
        self.hmm_model = HMM(n_states, n_emissions)
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.hmm_model.fit,
            X_train, y_train, settings.HMM_MAX_ITER
        )
        
        y_pred = self.hmm_model.predict(X_test)
        self.hmm_accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"HMM accuracy: {self.hmm_accuracy:.4f}")
    
    def predict_sentiment(self, text: str):
        if not self.training_completed:
            raise ValueError("Models not ready")
        
        text_vector = self.vectorizer.transform([text]).toarray()
        
        mlp_proba = self.mlp_model.predict_proba(text_vector)[0]
        mlp_pred = np.argmax(mlp_proba)
        mlp_confidence = float(np.max(mlp_proba))
        mlp_sentiment = self.label_encoder.inverse_transform([mlp_pred])[0]
        
        hmm_proba = self.hmm_model.predict_proba(text_vector)[0]
        hmm_pred = np.argmax(hmm_proba)
        hmm_confidence = float(np.max(hmm_proba))
        hmm_sentiment = self.label_encoder.inverse_transform([hmm_pred])[0]
        
        mlp_encoded = self._encode_for_db(mlp_pred)
        hmm_encoded = self._encode_for_db(hmm_pred)
        
        return {
            "mlp": {
                "sentiment": mlp_sentiment,
                "confidence": mlp_confidence,
                "encoded": mlp_encoded
            },
            "hmm": {
                "sentiment": hmm_sentiment,
                "confidence": hmm_confidence,
                "encoded": hmm_encoded
            }
        }
    
    def _encode_for_db(self, sentiment) -> str:
        if sentiment == 1:
            return "positif"
        elif sentiment == 0:
            return "negatif"
        else:  
            return sentiment