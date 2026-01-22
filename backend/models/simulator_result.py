"""
Simulator Result Model - Stores trading simulation outcomes for leaderboard
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class SimulatorResult(Base):
    """Stores each user's trading simulation result for the backtesting game."""
    __tablename__ = "simulator_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String(50), nullable=False)  # Denormalized for quick leaderboard queries
    
    # Trade configuration
    pair = Column(String(20), nullable=False)  # e.g., "BTC-USD"
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    
    # Position details
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=False)
    take_profit = Column(Float, nullable=False)
    
    # Results
    exit_price = Column(Float, nullable=False)
    pnl_percent = Column(Float, nullable=False)  # Profit/Loss percentage
    is_win = Column(Boolean, nullable=False)  # True if TP hit, False if SL hit
    hit_type = Column(String(10), nullable=False)  # "TP" or "SL" or "END" (if neither hit by end_date)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    
    # Indexes for leaderboard queries
    __table_args__ = (
        Index('idx_pnl_percent', 'pnl_percent'),
        Index('idx_user_pair', 'user_id', 'pair'),
        Index('idx_created_at_sim', 'created_at'),
    )

