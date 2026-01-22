"""
Price Prediction Models
Database models for storing price history and predictions
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Enum as SQLEnum
from sqlalchemy.sql import func
from database import Base
import enum


class PredictionTimeframe(str, enum.Enum):
    """Prediction timeframe options"""
    ONE_HOUR = "1h"
    TWENTY_FOUR_HOURS = "24h"
    SEVEN_DAYS = "7d"


class PredictionDirection(str, enum.Enum):
    """Prediction direction options"""
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class PriceHistory(Base):
    """Historical price data for analysis"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)  # BTC, ETH
    price = Column(Float, nullable=False)
    change_percent = Column(Float, default=0)
    volume = Column(Float, default=0)
    market_cap = Column(Float, default=0)
    source = Column(String(50))  # yahoo_finance, coingecko, binance
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class PricePrediction(Base):
    """AI-generated price predictions"""
    __tablename__ = "price_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)  # BTC, ETH
    timeframe = Column(SQLEnum(PredictionTimeframe), nullable=False)
    
    # Prediction details
    predicted_direction = Column(SQLEnum(PredictionDirection), nullable=False)
    predicted_change = Column(Float, nullable=False)  # Percentage
    confidence_score = Column(Integer, nullable=False)  # 0-100
    
    # Price data
    current_price = Column(Float, nullable=False)
    predicted_price = Column(Float, nullable=False)
    
    # AI reasoning
    reasoning = Column(Text)
    recommendation = Column(String(10))  # BUY, SELL, HOLD
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Accuracy tracking (filled in later when actual price is known)
    actual_price = Column(Float, nullable=True)
    accuracy_score = Column(Float, nullable=True)  # How close was the prediction
