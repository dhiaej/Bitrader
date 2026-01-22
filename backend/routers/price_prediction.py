"""
Price Prediction Router
API endpoints for smart price predictions
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from database import get_db
from services.price_prediction_service import price_prediction_service, PredictionTimeframe
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["Price Predictions"])


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    symbol: str
    timeframe: str
    prediction: str
    predicted_change: float
    confidence: int
    current_price: float
    predicted_price: float
    recommendation: str
    reasoning: str


@router.get("/all", response_model=Dict[str, Any])
async def get_all_predictions(
    force_refresh: bool = False,
    db: Session = Depends(get_db)
):
    """
    Get latest predictions for all cryptocurrencies (BTC, ETH, LTC, SOL, DOGE) and all timeframes (1h, 24h, 7d)
    
    Query Parameters:
    - force_refresh: If True, generates fresh predictions ignoring cache
    
    Returns predictions with confidence scores and recommendations
    """
    try:
        predictions = await price_prediction_service.get_all_predictions(db, force_refresh=force_refresh)
        return {
            "success": True,
            "predictions": predictions,
            "message": "AI predictions generated successfully"
        }
    except Exception as e:
        logger.error(f"Error getting predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/{timeframe}")
async def get_prediction(
    symbol: str,
    timeframe: PredictionTimeframe,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Get AI prediction for specific cryptocurrency and timeframe
    
    - **symbol**: BTC or ETH
    - **timeframe**: 1h, 24h, or 7d
    
    Returns prediction with confidence score, reasoning, and recommendation
    """
    try:
        symbol = symbol.upper()
        
        if symbol not in ["BTC", "ETH", "LTC", "SOL", "DOGE"]:
            raise HTTPException(status_code=400, detail="Symbol must be BTC, ETH, LTC, SOL, or DOGE")
        
        prediction = await price_prediction_service.generate_prediction(db, symbol, timeframe)
        
        if "error" in prediction:
            raise HTTPException(status_code=500, detail=prediction["error"])
        
        return {
            "success": True,
            "prediction": prediction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-history/{symbol}")
async def collect_price_history(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Manually trigger price history collection for a symbol
    (Normally done automatically in background)
    """
    try:
        symbol = symbol.upper()
        
        if symbol not in ["BTC", "ETH", "USDT"]:
            raise HTTPException(status_code=400, detail="Invalid symbol")
        
        await price_prediction_service.collect_historical_data(db, symbol)
        
        return {
            "success": True,
            "message": f"Price history collected for {symbol}"
        }
        
    except Exception as e:
        logger.error(f"Error collecting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
