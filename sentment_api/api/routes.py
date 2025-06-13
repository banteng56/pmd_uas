from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel
from datetime import datetime
import asyncpg
import logging
from typing import Optional, List, Dict, Any

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic Models
class PredictRequest(BaseModel):
    text: str

class NewsItem(BaseModel):
    title: Optional[str] = None
    img: Optional[str] = None
    hmm: Optional[str] = None
    mlp: Optional[str] = None

class NewsResponse(BaseModel):
    news: List[NewsItem]
    page: int
    limit: int
    total: Optional[int] = None
    has_more: bool

# Database connection function
async def get_db_connection():
    """Create database connection"""
    try:
        return await asyncpg.connect("postgres://postgres:password@localhost:5432/pmd")
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

# Original Routes
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "sentiment-analysis-consumer"
    }

@router.get("/models/status")
async def models_status(request: Request):
    """Get models training status"""
    model_trainer = request.app.state.model_trainer
    
    if not model_trainer:
        raise HTTPException(status_code=503, detail="Models not initialized")
    
    return {
        "training_completed": model_trainer.training_completed,
        "models": {
            "mlp": {
                "trained": model_trainer.mlp_model.is_trained if model_trainer.mlp_model else False,
                "accuracy": model_trainer.mlp_accuracy
            },
            "hmm": {
                "trained": model_trainer.hmm_model.is_trained if model_trainer.hmm_model else False,
                "accuracy": model_trainer.hmm_accuracy
            }
        },
        "vectorizer_vocab_size": len(model_trainer.vectorizer.vocabulary_) if model_trainer.vectorizer else 0,
        "label_classes": model_trainer.label_encoder.classes_.tolist() if model_trainer.label_encoder else []
    }

@router.post("/predict")
async def predict_sentiment(request: Request, data: PredictRequest):
    """Predict sentiment for given text"""
    model_trainer = request.app.state.model_trainer
    
    if not model_trainer or not model_trainer.training_completed:
        raise HTTPException(status_code=503, detail="Models not ready")
    
    try:
        predictions = model_trainer.predict_sentiment(data.text)
        return {
            "text": data.text,
            "predictions": predictions,
            "processed_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@router.get("/metrics")
async def get_metrics(request: Request):
    """Get consumer metrics"""
    consumer = request.app.state.consumer
    
    if not consumer:
        raise HTTPException(status_code=503, detail="Consumer not initialized")
    
    stats = consumer.get_stats()
    return {
        "consumer_stats": stats,
        "timestamp": datetime.now().isoformat()
    }

# News Routes
@router.get("/news", response_model=NewsResponse)
async def get_news(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sentiment_filter: Optional[str] = Query(None, description="Filter by sentiment (positive/negative/neutral)"),
    model_filter: Optional[str] = Query(None, description="Filter by model (hmm/mlp)")
):
    """
    Get news articles from PostgreSQL database with pagination and filtering
    """
    try:
        conn = await get_db_connection()
        
        offset = (page - 1) * limit
        
        # Base query
        base_query = """
        SELECT title, img, hmm, mlp 
        FROM articles 
        """
        
        count_query = "SELECT COUNT(*) FROM articles "
        params = []
        where_conditions = []
        param_count = 0
        
        # Add sentiment filter if provided
        if sentiment_filter:
            sentiment_filter = sentiment_filter.lower()
            if sentiment_filter in ['positive', 'negative', 'neutral']:
                if model_filter and model_filter.lower() in ['hmm', 'mlp']:
                    # Filter by specific model
                    param_count += 1
                    where_conditions.append(f"{model_filter.lower()} = ${param_count}")
                    params.append(sentiment_filter)
                else:
                    # Filter by either model
                    param_count += 1
                    where_conditions.append(f"(hmm = ${param_count} OR mlp = ${param_count})")
                    params.append(sentiment_filter)
        
        # Add model filter if provided (without sentiment filter)
        elif model_filter:
            model_filter = model_filter.lower()
            if model_filter in ['hmm', 'mlp']:
                param_count += 1
                where_conditions.append(f"{model_filter} IS NOT NULL")
        
        # Build WHERE clause
        where_clause = ""
        if where_conditions:
            where_clause = " WHERE " + " AND ".join(where_conditions)
        
        # Final queries
        param_count += 1
        limit_param = param_count
        param_count += 1
        offset_param = param_count
        
        final_query = base_query + where_clause + f" ORDER BY id DESC LIMIT ${limit_param} OFFSET ${offset_param}"
        final_count_query = count_query + where_clause
        
        # Execute queries
        params_with_pagination = params + [limit, offset]
        
        news_rows = await conn.fetch(final_query, *params_with_pagination)
        
        if params:
            total_count = await conn.fetchval(final_count_query, *params)
        else:
            total_count = await conn.fetchval(final_count_query)
        
        await conn.close()
        
        # Convert to response format
        news_items = []
        for row in news_rows:
            news_items.append(NewsItem(
                title=row['title'],
                img=row['img'],
                hmm=row['hmm'],
                mlp=row['mlp']
            ))
        
        has_more = len(news_items) == limit and (offset + limit) < total_count
        
        return NewsResponse(
            news=news_items,
            page=page,
            limit=limit,
            total=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Database error in get_news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/news/stats")
async def get_news_stats():
    """
    Get comprehensive news statistics
    """
    try:
        conn = await get_db_connection()
        
        stats_query = """
        SELECT 
            COUNT(*) as total_articles,
            COUNT(CASE WHEN title IS NOT NULL AND title != '' THEN 1 END) as with_title,
            COUNT(CASE WHEN img IS NOT NULL AND img != '' THEN 1 END) as with_images,
            COUNT(CASE WHEN hmm IS NOT NULL THEN 1 END) as hmm_analyzed,
            COUNT(CASE WHEN mlp IS NOT NULL THEN 1 END) as mlp_analyzed,
            COUNT(CASE WHEN hmm IS NOT NULL AND mlp IS NOT NULL THEN 1 END) as both_analyzed,
            COUNT(CASE WHEN hmm = 'positive' THEN 1 END) as hmm_positive,
            COUNT(CASE WHEN hmm = 'negative' THEN 1 END) as hmm_negative,
            COUNT(CASE WHEN hmm = 'neutral' THEN 1 END) as hmm_neutral,
            COUNT(CASE WHEN mlp = 'positive' THEN 1 END) as mlp_positive,
            COUNT(CASE WHEN mlp = 'negative' THEN 1 END) as mlp_negative,
            COUNT(CASE WHEN mlp = 'neutral' THEN 1 END) as mlp_neutral
        FROM articles
        """
        
        stats = await conn.fetchrow(stats_query)
        await conn.close()
        
        total = stats['total_articles']
        
        return {
            "total_articles": total,
            "data_coverage": {
                "with_title": {
                    "count": stats['with_title'],
                    "percentage": round((stats['with_title'] / total * 100) if total > 0 else 0, 2)
                },
                "with_images": {
                    "count": stats['with_images'],
                    "percentage": round((stats['with_images'] / total * 100) if total > 0 else 0, 2)
                },
                "hmm_analyzed": {
                    "count": stats['hmm_analyzed'],
                    "percentage": round((stats['hmm_analyzed'] / total * 100) if total > 0 else 0, 2)
                },
                "mlp_analyzed": {
                    "count": stats['mlp_analyzed'],
                    "percentage": round((stats['mlp_analyzed'] / total * 100) if total > 0 else 0, 2)
                },
                "both_analyzed": {
                    "count": stats['both_analyzed'],
                    "percentage": round((stats['both_analyzed'] / total * 100) if total > 0 else 0, 2)
                }
            },
            "sentiment_distribution": {
                "hmm": {
                    "positive": stats['hmm_positive'],
                    "negative": stats['hmm_negative'],
                    "neutral": stats['hmm_neutral'],
                    "total": stats['hmm_analyzed']
                },
                "mlp": {
                    "positive": stats['mlp_positive'],
                    "negative": stats['mlp_negative'],
                    "neutral": stats['mlp_neutral'],
                    "total": stats['mlp_analyzed']
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.get("/news/search", response_model=NewsResponse)
async def search_news(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sentiment_filter: Optional[str] = Query(None, description="Filter by sentiment")
):
    """
    Search news by title with optional sentiment filtering
    """
    try:
        conn = await get_db_connection()
        
        offset = (page - 1) * limit
        search_term = f"%{q}%"
        
        # Base queries
        base_query = """
        SELECT title, img, hmm, mlp 
        FROM articles 
        WHERE title ILIKE $1
        """
        
        count_query = """
        SELECT COUNT(*) 
        FROM articles 
        WHERE title ILIKE $1
        """
        
        params = [search_term]
        
        # Add sentiment filter if provided
        if sentiment_filter and sentiment_filter.lower() in ['positive', 'negative', 'neutral']:
            base_query += " AND (hmm = $2 OR mlp = $2)"
            count_query += " AND (hmm = $2 OR mlp = $2)"
            params.append(sentiment_filter.lower())
        
        # Add ordering and pagination
        search_query = base_query + f" ORDER BY id DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        params.extend([limit, offset])
        
        news_rows = await conn.fetch(search_query, *params)
        total_count = await conn.fetchval(count_query, *params[:-2])  # Exclude limit and offset for count
        
        await conn.close()
        
        news_items = []
        for row in news_rows:
            news_items.append(NewsItem(
                title=row['title'],
                img=row['img'],
                hmm=row['hmm'],
                mlp=row['mlp']
            ))
        
        has_more = len(news_items) == limit and (offset + limit) < total_count
        
        return NewsResponse(
            news=news_items,
            page=page,
            limit=limit,
            total=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@router.get("/news/sentiment-comparison")
async def get_sentiment_comparison(
    limit: int = Query(50, ge=1, le=200, description="Number of articles to compare")
):
    """
    Compare HMM vs MLP sentiment predictions
    """
    try:
        conn = await get_db_connection()
        
        comparison_query = """
        SELECT title, hmm, mlp,
               CASE 
                   WHEN hmm = mlp THEN 'agree'
                   WHEN hmm IS NULL OR mlp IS NULL THEN 'partial'
                   ELSE 'disagree'
               END as agreement
        FROM articles 
        WHERE hmm IS NOT NULL OR mlp IS NOT NULL
        ORDER BY id DESC
        LIMIT $1
        """
        
        rows = await conn.fetch(comparison_query, limit)
        
        # Calculate agreement statistics
        stats_query = """
        SELECT 
            COUNT(CASE WHEN hmm = mlp AND hmm IS NOT NULL AND mlp IS NOT NULL THEN 1 END) as agree,
            COUNT(CASE WHEN hmm != mlp AND hmm IS NOT NULL AND mlp IS NOT NULL THEN 1 END) as disagree,
            COUNT(CASE WHEN (hmm IS NULL AND mlp IS NOT NULL) OR (hmm IS NOT NULL AND mlp IS NULL) THEN 1 END) as partial,
            COUNT(CASE WHEN hmm IS NOT NULL AND mlp IS NOT NULL THEN 1 END) as both_available
        FROM articles
        """
        
        stats = await conn.fetchrow(stats_query)
        await conn.close()
        
        articles = []
        for row in rows:
            articles.append({
                "title": row['title'],
                "hmm": row['hmm'],
                "mlp": row['mlp'],
                "agreement": row['agreement']
            })
        
        total_compared = stats['both_available']
        agreement_rate = round((stats['agree'] / total_compared * 100) if total_compared > 0 else 0, 2)
        
        return {
            "articles": articles,
            "statistics": {
                "total_with_both_predictions": total_compared,
                "agreements": stats['agree'],
                "disagreements": stats['disagree'],
                "partial_predictions": stats['partial'],
                "agreement_rate_percentage": agreement_rate
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Sentiment comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sentiment comparison error: {str(e)}")

@router.get("/news/{article_id}")
async def get_single_news(article_id: int):
    """
    Get single news article by ID
    """
    try:
        conn = await get_db_connection()
        
        query = """
        SELECT title, img, hmm, mlp
        FROM articles 
        WHERE id = $1
        """
        
        row = await conn.fetchrow(query, article_id)
        await conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return NewsItem(
            title=row['title'],
            img=row['img'],
            hmm=row['hmm'],
            mlp=row['mlp']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get single news error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")