"""
Reputation service helpers - scoring, reviews, and badge generation.
"""

from __future__ import annotations

import json
from typing import List

from sqlalchemy.orm import Session

from config import settings
from models import Reputation, P2PTrade


def _clamp_score(value: float) -> int:
    return int(max(0, min(settings.MAX_REPUTATION_SCORE, round(value))))


def _generate_badges(rep: Reputation) -> List[str]:
    """
    Generate badges based on reputation metrics.
    Badges are awarded for various achievements and performance levels.
    """
    badges: List[str] = []
    
    # Safety checks for None values
    completed_trades = rep.completed_trades or 0
    total_trades = rep.total_trades or 0
    completion_rate = rep.completion_rate or 0.0
    average_rating = rep.average_rating or 0.0
    review_count = rep.review_count or 0
    disputed_trades = rep.disputed_trades or 0
    score = rep.score or 0
    
    # ===== TRADE VOLUME BADGES =====
    # Elite Trader: High volume + high completion rate
    if completed_trades >= 50 and completion_rate >= 85:
        badges.append("Elite Trader")
    # Active Trader: Regular activity
    elif completed_trades >= 10:
        badges.append("Active Trader")
    
    # Orderbook-specific badges
    if completed_trades >= 100:
        badges.append("Order Flow Pro")
    elif completed_trades >= 25:
        badges.append("Market Maker")
    
    # ===== RELIABILITY BADGES =====
    # Lightning Reliable: Near-perfect completion rate
    if completion_rate >= 95 and total_trades >= 10:
        badges.append("Lightning Reliable")
    # Consistent Closer: Good completion rate
    elif completion_rate >= 85 and total_trades >= 5:
        badges.append("Consistent Closer")
    
    # ===== REVIEW BADGES =====
    # Top Rated: Excellent reviews with enough feedback
    if average_rating >= 4.5 and review_count >= 5:
        badges.append("Top Rated")
    # Community Approved: Good reviews
    elif average_rating >= 4.0 and review_count >= 3:
        badges.append("Community Approved")
    
    # ===== TRUST BADGES =====
    # Trusted Partner: High overall score
    if score >= 250:
        badges.append("Trusted Partner")
    elif score >= 150:
        badges.append("Reliable Member")
    
    # ===== CLEAN RECORD BADGES =====
    # Zero Disputes: Clean trading record
    if disputed_trades == 0 and total_trades >= 5:
        badges.append("Zero Disputes")
    
    # ===== BEGINNER BADGES =====
    # First Trade: Completed first trade
    if completed_trades >= 1 and total_trades == completed_trades:
        badges.append("First Trade")
    
    # Remove duplicates while preserving order
    seen = set()
    unique_badges = []
    for badge in badges:
        if badge not in seen:
            unique_badges.append(badge)
            seen.add(badge)

    return unique_badges


def _store_badges(rep: Reputation) -> None:
    badges = _generate_badges(rep)
    rep.badges = json.dumps(badges) if badges else None


def ensure_reputation(db: Session, user_id: int) -> Reputation:
    """
    Ensure a reputation record exists for the user, creating it if necessary.
    
    Returns:
        Reputation object with all fields properly initialized
    """
    reputation = db.query(Reputation).filter(Reputation.user_id == user_id).first()
    if not reputation:
        reputation = Reputation(
            user_id=user_id,
            score=settings.INITIAL_REPUTATION_SCORE,
            total_trades=0,
            completed_trades=0,
            disputed_trades=0,
            completion_rate=0.0,
            average_rating=0.0,
            review_count=0,
            badges=None
        )
        db.add(reputation)
        db.flush()
    else:
        # Ensure all fields are initialized (handle None values from old records)
        if reputation.score is None:
            reputation.score = settings.INITIAL_REPUTATION_SCORE
        if reputation.total_trades is None:
            reputation.total_trades = 0
        if reputation.completed_trades is None:
            reputation.completed_trades = 0
        if reputation.disputed_trades is None:
            reputation.disputed_trades = 0
        if reputation.completion_rate is None:
            reputation.completion_rate = 0.0
        if reputation.average_rating is None:
            reputation.average_rating = 0.0
        if reputation.review_count is None:
            reputation.review_count = 0
    
    return reputation


def _record_trade_result(db: Session, user_id: int, *, success: bool, disputed: bool = False) -> None:
    """
    Record a trade result (success or failure) and update reputation accordingly.
    
    Args:
        db: Database session
        user_id: ID of the user whose reputation is being updated
        success: True if trade completed successfully, False if cancelled
        disputed: True if trade was disputed
    """
    reputation = ensure_reputation(db, user_id)
    
    # Initialize fields if None
    if reputation.total_trades is None:
        reputation.total_trades = 0
    if reputation.completed_trades is None:
        reputation.completed_trades = 0
    if reputation.disputed_trades is None:
        reputation.disputed_trades = 0
    if reputation.score is None:
        reputation.score = settings.INITIAL_REPUTATION_SCORE
    
    # Increment total trades
    reputation.total_trades += 1

    # Calculate score delta based on trade result
    if success:
        reputation.completed_trades += 1
        score_delta = settings.REPUTATION_TRADE_SUCCESS_POINTS
    else:
        # Trade cancelled
        score_delta = -settings.REPUTATION_TRADE_CANCEL_PENALTY

    # Handle disputes
    if disputed:
        reputation.disputed_trades += 1
        score_delta -= settings.REPUTATION_DISPUTE_PENALTY

    # Calculate completion rate (percentage of completed trades)
    if reputation.total_trades > 0:
        reputation.completion_rate = (reputation.completed_trades / reputation.total_trades) * 100.0
    else:
        reputation.completion_rate = 0.0

    # Update score with clamping
    new_score = reputation.score + score_delta
    reputation.score = _clamp_score(new_score)
    
    # Update badges after trade
    _store_badges(reputation)
    
    # Flush to ensure changes are in the session
    db.flush()
    
    # Debug log
    print(f"[REPUTATION] User {user_id}: {reputation.completed_trades} completed / {reputation.total_trades} total trades, score: {reputation.score}")


def record_trade_completion(db: Session, trade: P2PTrade) -> None:
    _record_trade_result(db, trade.buyer_id, success=True)
    _record_trade_result(db, trade.seller_id, success=True)


def record_trade_cancellation(db: Session, trade: P2PTrade) -> None:
    _record_trade_result(db, trade.buyer_id, success=False)
    _record_trade_result(db, trade.seller_id, success=False)


def record_trade_dispute(db: Session, trade: P2PTrade) -> None:
    _record_trade_result(db, trade.buyer_id, success=False, disputed=True)
    _record_trade_result(db, trade.seller_id, success=False, disputed=True)


def record_orderbook_trade(db: Session, buyer_id: int, seller_id: int) -> None:
    """Record completed trade originating from the order book"""
    try:
        print(f"[REPUTATION] Recording orderbook trade for buyer_id={buyer_id}, seller_id={seller_id}")
        
        # Record for buyer
        buyer_rep = ensure_reputation(db, buyer_id)
        before_buyer_completed = buyer_rep.completed_trades
        _record_trade_result(db, buyer_id, success=True)
        db.flush()
        db.refresh(buyer_rep)
        print(f"[REPUTATION] Buyer {buyer_id}: {before_buyer_completed} -> {buyer_rep.completed_trades} completed trades")
        
        # Record for seller
        seller_rep = ensure_reputation(db, seller_id)
        before_seller_completed = seller_rep.completed_trades
        _record_trade_result(db, seller_id, success=True)
        db.flush()
        db.refresh(seller_rep)
        print(f"[REPUTATION] Seller {seller_id}: {before_seller_completed} -> {seller_rep.completed_trades} completed trades")
        
        print(f"[REPUTATION] Trade recorded successfully")
    except Exception as e:
        print(f"[REPUTATION] ERROR recording trade: {e}")
        import traceback
        traceback.print_exc()
        raise


def apply_review_feedback(db: Session, reviewed_user_id: int, rating: int) -> None:
    """Apply review feedback and update reputation"""
    reputation = ensure_reputation(db, reviewed_user_id)
    
    # Calculate new average rating safely
    old_count = reputation.review_count or 0
    old_average = reputation.average_rating or 0.0
    new_count = old_count + 1
    
    if old_count == 0:
        # First review
        reputation.average_rating = float(rating)
    else:
        # Update average: (old_avg * old_count + new_rating) / new_count
        reputation.average_rating = ((old_average * old_count) + rating) / new_count
    
    reputation.review_count = new_count
    
    # Reward good ratings, penalize bad ones
    # Rating 1-2: penalty, 3: neutral, 4-5: bonus
    score_delta = (rating - 3) * settings.REPUTATION_REVIEW_WEIGHT
    reputation.score = _clamp_score(reputation.score + score_delta)
    
    # Update badges after review
    _store_badges(reputation)
    
    # Flush to ensure changes are saved
    db.flush()


def parse_badges(reputation: Reputation) -> List[str]:
    if reputation.badges:
        try:
            return json.loads(reputation.badges)
        except json.JSONDecodeError:
            return []
    return []

