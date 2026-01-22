"""
Admin Router - Admin dashboard endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional
import json
from datetime import datetime, timedelta, date

from database import get_db
from models import (
    User, Wallet, Transaction, OrderBookOrder, Trade, 
    P2PAdvertisement, P2PTrade, Dispute, Reputation, Review, P2PTradeStatus,
    SuspiciousEvent, SuspiciousEventStatus, SuspiciousTransactionType,
    Escrow, DisputeStatus
)
from schemas import UserResponse, SuspiciousEventListResponse, SuspiciousEventResponse, SuspiciousEventUpdate
from utils.auth import get_current_admin

router = APIRouter()


def _serialize_suspicious_event(event: SuspiciousEvent) -> SuspiciousEventResponse:
    try:
        features_snapshot = json.loads(event.features_snapshot) if event.features_snapshot else None
    except json.JSONDecodeError:
        features_snapshot = None
    try:
        rules_triggered = json.loads(event.rules_triggered) if event.rules_triggered else None
    except json.JSONDecodeError:
        rules_triggered = None

    data = {
        "id": event.id,
        "transaction_id": event.transaction_id,
        "transaction_type": event.transaction_type.value if event.transaction_type else None,
        "user_id": event.user_id,
        "counterparty_id": event.counterparty_id,
        "score": event.score,
        "rules_triggered": rules_triggered,
        "features_snapshot": features_snapshot,
        "explanation": event.explanation,
        "status": event.status.value if event.status else None,
        "admin_notes": event.admin_notes,
        "created_at": event.created_at,
        "updated_at": event.updated_at,
    }
    return SuspiciousEventResponse(**data)


@router.get("/stats/overview")
async def get_overview_stats(
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get overall platform statistics"""
    
    # User statistics
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    verified_users = db.query(func.count(User.id)).filter(User.is_verified == True).scalar() or 0
    
    # SQLite-compatible date filter for today (use Python's date comparison)
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    new_users_today = db.query(func.count(User.id)).filter(
        User.created_at >= today_start,
        User.created_at <= today_end
    ).scalar() or 0
    
    new_users_this_week = db.query(func.count(User.id)).filter(
        User.created_at >= datetime.utcnow() - timedelta(days=7)
    ).scalar() or 0
    
    # Trade statistics
    total_orderbook_trades = db.query(func.count(Trade.id)).scalar() or 0
    total_p2p_trades = db.query(func.count(P2PTrade.id)).scalar() or 0
    completed_p2p_trades = db.query(func.count(P2PTrade.id)).filter(
        P2PTrade.status == P2PTradeStatus.COMPLETED
    ).scalar() or 0
    
    # Financial statistics
    total_transactions = db.query(func.count(Transaction.id)).scalar() or 0
    total_volume_usd = db.query(func.sum(Transaction.amount)).filter(
        Transaction.currency == "USD"
    ).scalar() or 0
    
    # Orders statistics
    pending_orders = db.query(func.count(OrderBookOrder.id)).filter(
        OrderBookOrder.status == "PENDING"
    ).scalar() or 0
    total_orders = db.query(func.count(OrderBookOrder.id)).scalar() or 0
    
    # P2P Ads
    active_p2p_ads = db.query(func.count(P2PAdvertisement.id)).filter(
        P2PAdvertisement.is_active == True
    ).scalar() or 0
    total_p2p_ads = db.query(func.count(P2PAdvertisement.id)).scalar() or 0
    
    # Disputes
    open_disputes = db.query(func.count(Dispute.id)).filter(
        Dispute.status == "OPEN"
    ).scalar() or 0
    total_disputes = db.query(func.count(Dispute.id)).scalar() or 0
    
    # Reputation
    avg_reputation_score = db.query(func.avg(Reputation.score)).scalar() or 0
    total_reviews = db.query(func.count(Review.id)).scalar() or 0
    
    return {
        "users": {
            "total": total_users,
            "active": active_users,
            "verified": verified_users,
            "new_today": new_users_today,
            "new_this_week": new_users_this_week
        },
        "trades": {
            "orderbook_total": total_orderbook_trades,
            "p2p_total": total_p2p_trades,
            "p2p_completed": completed_p2p_trades,
            "p2p_completion_rate": (completed_p2p_trades / total_p2p_trades * 100) if total_p2p_trades > 0 else 0
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders
        },
        "p2p_ads": {
            "total": total_p2p_ads,
            "active": active_p2p_ads
        },
        "disputes": {
            "total": total_disputes,
            "open": open_disputes
        },
        "financial": {
            "total_transactions": total_transactions,
            "total_volume_usd": float(total_volume_usd)
        },
        "reputation": {
            "avg_score": float(avg_reputation_score),
            "total_reviews": total_reviews
        }
    }


@router.get("/suspicious-events", response_model=SuspiciousEventListResponse)
async def list_suspicious_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = None,
    min_score: Optional[float] = None,
    transaction_type: Optional[str] = None,
    user_id: Optional[int] = None,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    query = db.query(SuspiciousEvent)

    if status_filter:
        try:
            status_enum = SuspiciousEventStatus(status_filter.upper())
            query = query.filter(SuspiciousEvent.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status filter")

    if min_score is not None:
        query = query.filter(SuspiciousEvent.score >= min_score)

    if transaction_type:
        try:
            tx_type_enum = SuspiciousTransactionType(transaction_type.upper())
            query = query.filter(SuspiciousEvent.transaction_type == tx_type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid transaction type filter")

    if user_id:
        query = query.filter(SuspiciousEvent.user_id == user_id)

    total = query.count()
    events = (
        query.order_by(desc(SuspiciousEvent.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "events": [_serialize_suspicious_event(event) for event in events]
    }


@router.put("/suspicious-events/{event_id}", response_model=SuspiciousEventResponse)
async def update_suspicious_event(
    event_id: int,
    payload: SuspiciousEventUpdate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    event = db.query(SuspiciousEvent).filter(SuspiciousEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Suspicious event not found")

    if payload.status:
        try:
            event.status = SuspiciousEventStatus(payload.status.upper())
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status value")

    if payload.admin_notes is not None:
        event.admin_notes = payload.admin_notes

    db.commit()
    db.refresh(event)
    return _serialize_suspicious_event(event)


@router.get("/users")
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all users with pagination and filters"""
    
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (User.full_name.ilike(f"%{search}%"))
        )
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_admin is not None:
        query = query.filter(User.is_admin == is_admin)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    users = query.order_by(desc(User.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "users": [UserResponse.model_validate(user) for user in users]
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: int,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed information about a specific user"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's statistics
    wallet_count = db.query(func.count(Wallet.id)).filter(Wallet.user_id == user_id).scalar() or 0
    order_count = db.query(func.count(OrderBookOrder.id)).filter(OrderBookOrder.user_id == user_id).scalar() or 0
    p2p_ad_count = db.query(func.count(P2PAdvertisement.id)).filter(P2PAdvertisement.user_id == user_id).scalar() or 0
    p2p_trade_count = db.query(func.count(P2PTrade.id)).filter(
        (P2PTrade.buyer_id == user_id) | (P2PTrade.seller_id == user_id)
    ).scalar() or 0
    
    reputation = db.query(Reputation).filter(Reputation.user_id == user_id).first()
    
    return {
        "user": UserResponse.model_validate(user),
        "stats": {
            "wallets": wallet_count,
            "orders": order_count,
            "p2p_ads": p2p_ad_count,
            "p2p_trades": p2p_trade_count,
            "reputation": {
                "score": reputation.score if reputation else 0,
                "total_trades": reputation.total_trades if reputation else 0,
                "completed_trades": reputation.completed_trades if reputation else 0,
                "average_rating": reputation.average_rating if reputation else 0.0
            }
        }
    }


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle user active status"""
    
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"User {'activated' if user.is_active else 'deactivated'} successfully",
        "user": UserResponse.model_validate(user)
    }


@router.put("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: int,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Toggle user admin status"""
    
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove admin privileges from yourself"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.is_admin = not user.is_admin
    db.commit()
    db.refresh(user)
    
    return {
        "message": f"User admin status {'granted' if user.is_admin else 'revoked'} successfully",
        "user": UserResponse.model_validate(user)
    }


@router.get("/trades/recent")
async def get_recent_trades(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get recent trades (orderbook and P2P)"""
    
    # Orderbook trades
    orderbook_trades = db.query(Trade).order_by(desc(Trade.created_at)).offset(skip).limit(limit).all()
    
    # P2P trades
    p2p_trades = db.query(P2PTrade).order_by(desc(P2PTrade.created_at)).offset(skip).limit(limit).all()
    
    return {
        "orderbook_trades": [
            {
                "id": t.id,
                "buyer_id": t.buyer_id,
                "seller_id": t.seller_id,
                "instrument": t.instrument,
                "price": float(t.price),
                "quantity": float(t.quantity),
                "total_amount": float(t.total_amount),
                "created_at": t.created_at.isoformat()
            }
            for t in orderbook_trades
        ],
        "p2p_trades": [
            {
                "id": t.id,
                "buyer_id": t.buyer_id,
                "seller_id": t.seller_id,
                "currency": t.currency,
                "amount": float(t.amount),
                "price": float(t.price),
                "status": t.status.value,
                "created_at": t.created_at.isoformat()
            }
            for t in p2p_trades
        ]
    }


@router.get("/disputes")
async def get_all_disputes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = None,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get all disputes"""
    
    query = db.query(Dispute)
    
    if status_filter:
        query = query.filter(Dispute.status == status_filter)
    
    total = query.count()
    disputes = query.order_by(desc(Dispute.created_at)).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "disputes": [
            {
                "id": d.id,
                "trade_id": d.trade_id,
                "filed_by": d.filed_by,
                "reason": d.reason,
                "status": d.status.value,
                "created_at": d.created_at.isoformat(),
                "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None
            }
            for d in disputes
        ]
    }


@router.get("/disputes/{dispute_id}")
async def get_dispute_details(
    dispute_id: int,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get detailed dispute information including trade, parties, and escrow details"""
    
    # Get dispute
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Get trade with all related data
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Get buyer and seller details
    buyer = db.query(User).filter(User.id == trade.buyer_id).first()
    seller = db.query(User).filter(User.id == trade.seller_id).first()
    
    # Get escrow details if exists
    escrow = None
    escrow_data = None
    if trade.escrow_id:
        escrow = db.query(Escrow).filter(Escrow.id == trade.escrow_id).first()
    
    if escrow:
        escrow_data = {
            "id": escrow.id,
            "amount": float(escrow.amount),
            "currency": escrow.currency,
            "status": escrow.status,
            "locked_at": escrow.locked_at.isoformat() if escrow.locked_at else None,
            "released_at": escrow.released_at.isoformat() if escrow.released_at else None
        }
    
    # Parse evidence
    evidence_list = []
    if dispute.evidence:
        try:
            import json
            evidence_list = json.loads(dispute.evidence)
        except:
            evidence_list = [dispute.evidence]
    
    return {
        "dispute": {
            "id": dispute.id,
            "trade_id": dispute.trade_id,
            "filed_by": dispute.filed_by,
            "reason": dispute.reason,
            "evidence": dispute.evidence,
            "status": dispute.status.value,
            "resolution": dispute.resolution,
            "resolved_by": dispute.resolved_by,
            "created_at": dispute.created_at.isoformat(),
            "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
        },
        "trade": {
            "id": trade.id,
            "amount": float(trade.amount),
            "currency": trade.currency,
            "fiat_currency": trade.fiat_currency,
            "price": float(trade.price),
            "total_fiat": float(trade.total_fiat),
            "status": trade.status.value,
            "payment_method": trade.payment_method,
            "created_at": trade.created_at.isoformat()
        },
        "buyer": {
            "id": buyer.id,
            "username": buyer.username,
            "email": buyer.email,
            "is_active": buyer.is_active
        } if buyer else None,
        "seller": {
            "id": seller.id,
            "username": seller.username,
            "email": seller.email,
            "is_active": seller.is_active
        } if seller else None,
        "escrow": escrow_data
    }


@router.put("/disputes/{dispute_id}/resolve")
async def resolve_dispute_admin(
    dispute_id: int,
    resolution_data: dict,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Resolve a dispute (admin endpoint)"""
    
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    if dispute.status == DisputeStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispute already resolved"
        )
    
    # Get trade
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Get escrow if exists
    escrow = None
    if trade.escrow_id:
        escrow = db.query(Escrow).filter(Escrow.id == trade.escrow_id).first()
    
    # Resolve based on decision
    refund_to_buyer = resolution_data.get("refund_to_buyer", False)
    release_to_seller = resolution_data.get("release_to_seller", False)
    
    if refund_to_buyer:
        # Buyer wins - refund buyer (trade cancelled)
        trade.status = P2PTradeStatus.CANCELLED
        if escrow:
            escrow.status = "REFUNDED"
            escrow.released_at = datetime.utcnow()
        
    elif release_to_seller:
        # Seller wins - release crypto to buyer (trade completes)
        trade.status = P2PTradeStatus.COMPLETED
        trade.completed_at = datetime.utcnow()
        if escrow:
            escrow.status = "RELEASED"
            escrow.released_at = datetime.utcnow()
    
    # Update dispute
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = resolution_data.get("resolution", "")
    dispute.resolved_by = admin_user.id
    dispute.resolved_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Dispute resolved successfully"}

