"""Reputation Router"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import User, Reputation, Review, P2PTrade, P2PTradeStatus
from schemas import (
    ReputationResponse,
    ReputationProfileResponse,
    ReviewCreate,
    ReviewResponse,
    PublicUserProfile,
    ReviewedTradesResponse,
)
from utils.auth import get_current_user
from services.reputation_service import (
    ensure_reputation,
    apply_review_feedback,
    parse_badges,
)

router = APIRouter()


def _serialize_user(user: User) -> PublicUserProfile:
    return PublicUserProfile(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
    )


def _serialize_reputation(rep: Reputation) -> ReputationResponse:
    data = {
        "id": rep.id,
        "user_id": rep.user_id,
        "score": rep.score,
        "total_trades": rep.total_trades,
        "completed_trades": rep.completed_trades,
        "disputed_trades": rep.disputed_trades,
        "completion_rate": rep.completion_rate,
        "average_response_time": rep.average_response_time,
        "average_rating": rep.average_rating,
        "review_count": rep.review_count,
        "badges": parse_badges(rep),
    }
    return ReputationResponse(**data)


def _build_profile(user: User, db: Session, review_limit: int = 5) -> ReputationProfileResponse:
    reputation = ensure_reputation(db, user.id)
    recent_reviews = (
        db.query(Review)
        .filter(Review.reviewed_user_id == user.id)
        .order_by(Review.created_at.desc())
        .limit(review_limit)
        .all()
    )
    return ReputationProfileResponse(
        user=_serialize_user(user),
        reputation=_serialize_reputation(reputation),
        recent_reviews=[ReviewResponse.model_validate(review) for review in recent_reviews],
    )


@router.get("/me", response_model=ReputationProfileResponse)
async def get_my_reputation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get reputation summary for the authenticated user"""
    return _build_profile(current_user, db)


@router.get("/user/{username}", response_model=ReputationProfileResponse)
async def get_user_reputation(username: str, db: Session = Depends(get_db)):
    """Get public reputation profile for a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _build_profile(user, db)


@router.get(
    "/user/{username}/reviews",
    response_model=List[ReviewResponse],
)
async def list_user_reviews(
    username: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List reviews received by a user"""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    reviews = (
        db.query(Review)
        .filter(Review.reviewed_user_id == user.id)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )
    return [ReviewResponse.model_validate(review) for review in reviews]


@router.post("/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a review after a completed trade"""
    trade = db.query(P2PTrade).filter(P2PTrade.id == payload.trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    if trade.status != P2PTradeStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Trade is not completed yet")

    if current_user.id not in {trade.buyer_id, trade.seller_id}:
        raise HTTPException(status_code=403, detail="You are not part of this trade")

    reviewed_user_id = trade.seller_id if current_user.id == trade.buyer_id else trade.buyer_id

    existing_review = db.query(Review).filter(
        Review.trade_id == trade.id,
        Review.reviewer_id == current_user.id
    ).first()

    if existing_review:
        raise HTTPException(status_code=400, detail="You already reviewed this trade")

    review = Review(
        trade_id=trade.id,
        reviewer_id=current_user.id,
        reviewed_user_id=reviewed_user_id,
        rating=payload.rating,
        comment=payload.comment
    )
    db.add(review)

    apply_review_feedback(db, reviewed_user_id, payload.rating)

    db.commit()
    db.refresh(review)

    return ReviewResponse.model_validate(review)


@router.get("/reviews/my/trades", response_model=ReviewedTradesResponse)
async def get_reviewed_trade_ids(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return trade IDs that the current user has already reviewed"""
    trade_ids = [
        row[0] for row in db.query(Review.trade_id).filter(Review.reviewer_id == current_user.id).all()
    ]
    return ReviewedTradesResponse(trade_ids=trade_ids)
