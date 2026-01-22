"""
P2P Trading Router - Advertisements, P2P trades, escrow
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
import json

from database import get_db
from models import User, P2PAdvertisement, P2PTrade, Escrow, Wallet, Transaction, TransactionType, OrderType, P2PTradeStatus, Notification
from schemas import P2PAdCreate, P2PAdResponse, P2PTradeCreate, P2PTradeResponse
from utils.auth import get_current_user
from config import settings

router = APIRouter()


def create_auto_trade(db: Session, ad1: P2PAdvertisement, ad2: P2PAdvertisement, amount: Decimal, initiator_id: int):
    """Helper function to create automatic trade from matched ads"""
    
    # Determine buyer and seller
    if ad1.ad_type == OrderType.SELL:
        seller_ad = ad1
        buyer_ad = ad2
    else:
        seller_ad = ad2
        buyer_ad = ad1
    
    buyer_id = buyer_ad.user_id
    seller_id = seller_ad.user_id
    
    # Calculate fiat total
    total_fiat = amount * seller_ad.price
    
    # Create escrow
    escrow = Escrow(
        amount=amount,
        currency=seller_ad.currency,
        status="LOCKED"
    )
    db.add(escrow)
    db.flush()
    
    # Lock seller's funds
    seller_wallet = db.query(Wallet).filter(
        Wallet.user_id == seller_id,
        Wallet.currency == seller_ad.currency
    ).first()
    
    if seller_wallet and seller_wallet.available_balance >= amount:
        seller_wallet.available_balance -= amount
        seller_wallet.locked_balance += amount
    
    # Create trade
    payment_deadline = datetime.utcnow() + timedelta(minutes=seller_ad.payment_time_limit)
    common_payment_methods = list(set(json.loads(ad1.payment_methods)) & set(json.loads(ad2.payment_methods)))
    
    new_trade = P2PTrade(
        advertisement_id=seller_ad.id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        amount=amount,
        price=seller_ad.price,
        total_fiat=total_fiat,
        currency=seller_ad.currency,
        fiat_currency=seller_ad.fiat_currency,
        status=P2PTradeStatus.PENDING,
        payment_method=common_payment_methods[0] if common_payment_methods else json.loads(seller_ad.payment_methods)[0],
        escrow_id=escrow.id,
        payment_deadline=payment_deadline
    )
    db.add(new_trade)
    db.flush()
    
    # Update advertisement amounts
    ad1.available_amount -= amount
    ad2.available_amount -= amount
    
    # Get usernames for notifications
    buyer_user = db.query(User).filter(User.id == buyer_id).first()
    seller_user = db.query(User).filter(User.id == seller_id).first()
    buyer_username = buyer_user.username if buyer_user else "Unknown"
    seller_username = seller_user.username if seller_user else "Unknown"
    
    # Create notifications for both users
    buyer_notification = Notification(
        user_id=buyer_id,
        type="P2P_MATCH",
        title="P2P Trade Matched!",
        message=f"Your BUY ad has been automatically matched with {seller_username}! {amount} {seller_ad.currency} at {seller_ad.price} {seller_ad.fiat_currency}",
        data=json.dumps({
            "trade_id": new_trade.id,
            "amount": str(amount),
            "price": str(seller_ad.price),
            "currency": seller_ad.currency,
            "total_fiat": str(total_fiat),
            "payment_deadline": payment_deadline.isoformat(),
            "trading_with": seller_username,
            "trading_with_id": seller_id
        })
    )
    
    seller_notification = Notification(
        user_id=seller_id,
        type="P2P_MATCH",
        title="P2P Trade Matched!",
        message=f"Your SELL ad has been automatically matched with {buyer_username}! {amount} {seller_ad.currency} at {seller_ad.price} {seller_ad.fiat_currency}",
        data=json.dumps({
            "trade_id": new_trade.id,
            "amount": str(amount),
            "price": str(seller_ad.price),
            "currency": seller_ad.currency,
            "total_fiat": str(total_fiat),
            "payment_deadline": payment_deadline.isoformat(),
            "trading_with": buyer_username,
            "trading_with_id": buyer_id
        })
    )
    
    db.add(buyer_notification)
    db.add(seller_notification)
    
    return new_trade


@router.post("/advertisements", response_model=P2PAdResponse, status_code=status.HTTP_201_CREATED)
async def create_advertisement(
    ad_data: P2PAdCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create P2P advertisement with automatic matching"""
    
    # Validate wallet balance if selling
    if ad_data.ad_type == "SELL":
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.currency == ad_data.currency
        ).first()
        
        if not wallet or wallet.available_balance < Decimal(str(ad_data.available_amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient {ad_data.currency} balance"
            )
    
    # Create advertisement first
    new_ad = P2PAdvertisement(
        user_id=current_user.id,
        ad_type=OrderType(ad_data.ad_type),
        currency=ad_data.currency,
        fiat_currency=ad_data.fiat_currency,
        price=Decimal(str(ad_data.price)),
        min_limit=Decimal(str(ad_data.min_limit)),
        max_limit=Decimal(str(ad_data.max_limit)),
        available_amount=Decimal(str(ad_data.available_amount)),
        payment_methods=json.dumps(ad_data.payment_methods),
        payment_time_limit=ad_data.payment_time_limit,
        terms_conditions=ad_data.terms_conditions
    )
    
    db.add(new_ad)
    db.flush()  # Get the ID without committing
    
    # ===== AUTO-MATCHING LOGIC =====
    # Find opposite type advertisements with exact match
    opposite_type = OrderType.BUY if ad_data.ad_type == "SELL" else OrderType.SELL
    
    # Parse payment methods
    new_payment_methods = set(ad_data.payment_methods)
    
    # Find matching advertisements
    potential_matches = db.query(P2PAdvertisement).filter(
        P2PAdvertisement.user_id != current_user.id,
        P2PAdvertisement.ad_type == opposite_type,
        P2PAdvertisement.currency == ad_data.currency,
        P2PAdvertisement.fiat_currency == ad_data.fiat_currency,
        P2PAdvertisement.price == Decimal(str(ad_data.price)),
        P2PAdvertisement.is_active == True
    ).all()
    
    matched_ad = None
    for ad in potential_matches:
        # Check payment method compatibility
        ad_payment_methods = set(json.loads(ad.payment_methods))
        if new_payment_methods & ad_payment_methods:  # Intersection
            matched_ad = ad
            break
    
    if matched_ad:
        # EXACT MATCH FOUND - Create automatic trade
        match_amount = min(new_ad.available_amount, matched_ad.available_amount)
        
        if match_amount == new_ad.available_amount and match_amount == matched_ad.available_amount:
            # PERFECT EXACT MATCH
            trade = create_auto_trade(db, new_ad, matched_ad, match_amount, current_user.id)
            new_ad.is_active = False
            matched_ad.is_active = False
            
        elif match_amount < new_ad.available_amount or match_amount < matched_ad.available_amount:
            # PARTIAL MATCH - Send notification to user with larger amount
            larger_ad = new_ad if new_ad.available_amount > matched_ad.available_amount else matched_ad
            larger_user_id = larger_ad.user_id
            smaller_ad = matched_ad if larger_ad.id == new_ad.id else new_ad
            smaller_user_id = smaller_ad.user_id
            
            # Create notification for user with larger amount
            notification = Notification(
                user_id=larger_user_id,
                type="PARTIAL_MATCH",
                title="Partial P2P Match Found",
                message=f"A partial match was found for your {larger_ad.ad_type.value} ad. {match_amount} {larger_ad.currency} can be matched at {larger_ad.price} {larger_ad.fiat_currency}",
                data=json.dumps({
                    "your_ad_id": larger_ad.id,
                    "match_ad_id": smaller_ad.id,
                    "match_amount": str(match_amount),
                    "your_amount": str(larger_ad.available_amount),
                    "match_user_id": smaller_user_id
                })
            )
            db.add(notification)
    
    db.commit()
    db.refresh(new_ad)
    
    return new_ad


@router.get("/advertisements", response_model=List[P2PAdResponse])
async def get_advertisements(
    ad_type: Optional[str] = None,
    currency: Optional[str] = None,
    fiat_currency: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get P2P advertisements with filters
    
    Query Parameters:
    - ad_type: Filter by BUY or SELL
    - currency: Filter by crypto currency (BTC, ETH, USDT)
    - fiat_currency: Filter by fiat currency (USD, EUR, GBP)
    - min_amount: Minimum limit amount
    - max_amount: Maximum limit amount
    - is_active: Filter by active status (true/false/null for all)
    - search: Search in payment methods and terms
    - limit: Number of results to return
    - offset: Pagination offset
    """
    
    query = db.query(P2PAdvertisement)
    
    # Filter by active status (if not specified, show only active by default)
    if is_active is None:
        query = query.filter(P2PAdvertisement.is_active == True)
    elif is_active is not None:
        query = query.filter(P2PAdvertisement.is_active == is_active)
    
    if ad_type:
        query = query.filter(P2PAdvertisement.ad_type == ad_type.upper())
    
    if currency:
        query = query.filter(P2PAdvertisement.currency == currency.upper())
    
    if fiat_currency:
        query = query.filter(P2PAdvertisement.fiat_currency == fiat_currency.upper())
    
    if min_amount:
        query = query.filter(P2PAdvertisement.min_limit >= min_amount)
    
    if max_amount:
        query = query.filter(P2PAdvertisement.max_limit <= max_amount)
    
    # Search in payment methods, terms/conditions, currency, and fiat currency
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                P2PAdvertisement.payment_methods.like(search_pattern),
                P2PAdvertisement.terms_conditions.like(search_pattern),
                P2PAdvertisement.currency.like(search_pattern),
                P2PAdvertisement.fiat_currency.like(search_pattern),
                P2PAdvertisement.ad_type.like(search_pattern)
            )
        )
    
    ads = query.order_by(desc(P2PAdvertisement.created_at)).offset(offset).limit(limit).all()
    
    return ads


@router.get("/advertisements/{ad_id}", response_model=P2PAdResponse)
async def get_advertisement(ad_id: int, db: Session = Depends(get_db)):
    """Get specific advertisement"""
    ad = db.query(P2PAdvertisement).filter(P2PAdvertisement.id == ad_id).first()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertisement not found"
        )
    
    return ad


@router.delete("/advertisements/{ad_id}")
async def delete_advertisement(
    ad_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete/deactivate advertisement"""
    ad = db.query(P2PAdvertisement).filter(
        P2PAdvertisement.id == ad_id,
        P2PAdvertisement.user_id == current_user.id
    ).first()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertisement not found"
        )
    
    ad.is_active = False
    db.commit()
    
    return {"message": "Advertisement deactivated successfully"}


@router.post("/trades", response_model=P2PTradeResponse, status_code=status.HTTP_201_CREATED)
async def initiate_trade(
    trade_data: P2PTradeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Initiate P2P trade from advertisement"""
    
    # Get advertisement
    ad = db.query(P2PAdvertisement).filter(
        P2PAdvertisement.id == trade_data.advertisement_id,
        P2PAdvertisement.is_active == True
    ).first()
    
    if not ad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Advertisement not found or inactive"
        )
    
    if ad.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot trade with your own advertisement"
        )
    
    # Validate amount - amount is in FIAT currency
    fiat_amount = Decimal(str(trade_data.amount))
    
    # Check fiat limits
    if fiat_amount < ad.min_limit or fiat_amount > ad.max_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount must be between {ad.min_limit} and {ad.max_limit} {ad.fiat_currency}"
        )
    
    # Calculate crypto amount from fiat
    crypto_amount = fiat_amount / ad.price
    
    # Check if enough crypto available
    if crypto_amount > ad.available_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient crypto available. Maximum: {ad.available_amount} {ad.currency}"
        )
    
    # Determine buyer and seller
    if ad.ad_type == OrderType.SELL:
        buyer_id = current_user.id
        seller_id = ad.user_id
    else:
        buyer_id = ad.user_id
        seller_id = current_user.id
    
    # Create escrow
    escrow = Escrow(
        amount=crypto_amount,
        currency=ad.currency,
        status="LOCKED"
    )
    db.add(escrow)
    db.flush()
    
    # Lock seller's funds
    seller_wallet = db.query(Wallet).filter(
        Wallet.user_id == seller_id,
        Wallet.currency == ad.currency
    ).first()
    
    if not seller_wallet or seller_wallet.available_balance < crypto_amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seller has insufficient balance"
        )
    
    seller_wallet.available_balance -= crypto_amount
    seller_wallet.locked_balance += crypto_amount
    
    # Create trade
    payment_deadline = datetime.utcnow() + timedelta(minutes=ad.payment_time_limit)
    
    new_trade = P2PTrade(
        advertisement_id=ad.id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        amount=crypto_amount,
        price=ad.price,
        total_fiat=fiat_amount,
        currency=ad.currency,
        fiat_currency=ad.fiat_currency,
        status=P2PTradeStatus.PENDING,
        payment_method=trade_data.payment_method,
        escrow_id=escrow.id,
        payment_deadline=payment_deadline
    )
    
    db.add(new_trade)
    
    # Update advertisement available amount
    ad.available_amount -= crypto_amount
    if ad.available_amount <= 0:
        ad.is_active = False
    
    db.commit()
    db.refresh(new_trade)
    
    return new_trade


@router.get("/trades", response_model=List[P2PTradeResponse])
async def get_user_trades(
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's P2P trades"""
    query = db.query(P2PTrade).filter(
        or_(
            P2PTrade.buyer_id == current_user.id,
            P2PTrade.seller_id == current_user.id
        )
    )
    
    if status_filter:
        query = query.filter(P2PTrade.status == status_filter.upper())
    
    trades = query.order_by(desc(P2PTrade.created_at)).limit(limit).all()
    return trades


@router.post("/trades/{trade_id}/payment-sent")
async def mark_payment_sent(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Buyer marks payment as sent"""
    trade = db.query(P2PTrade).filter(
        P2PTrade.id == trade_id,
        P2PTrade.buyer_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    if trade.status != P2PTradeStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Trade is not in pending status"
        )
    
    trade.status = P2PTradeStatus.PAYMENT_SENT
    db.commit()
    
    return {"message": "Payment marked as sent"}


@router.post("/trades/{trade_id}/confirm-payment")
async def confirm_payment(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Seller confirms payment received - releases escrow"""
    trade = db.query(P2PTrade).filter(
        P2PTrade.id == trade_id,
        P2PTrade.seller_id == current_user.id
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    if trade.status != P2PTradeStatus.PAYMENT_SENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment must be marked as sent first"
        )
    
    # Release escrow
    escrow = db.query(Escrow).filter(Escrow.id == trade.escrow_id).first()
    if escrow:
        escrow.status = "RELEASED"
        escrow.released_at = datetime.utcnow()
    
    # Transfer crypto funds
    seller_wallet = db.query(Wallet).filter(
        Wallet.user_id == trade.seller_id,
        Wallet.currency == trade.currency
    ).first()
    
    buyer_wallet = db.query(Wallet).filter(
        Wallet.user_id == trade.buyer_id,
        Wallet.currency == trade.currency
    ).first()
    
    if seller_wallet:
        seller_wallet.locked_balance -= trade.amount
    
    if buyer_wallet:
        buyer_wallet.available_balance += trade.amount
    else:
        # Create wallet if doesn't exist
        buyer_wallet = Wallet(
            user_id=trade.buyer_id,
            currency=trade.currency,
            available_balance=trade.amount,
            locked_balance=0
        )
        db.add(buyer_wallet)
        db.flush()
    
    # Transfer fiat funds (opposite direction)
    seller_fiat_wallet = db.query(Wallet).filter(
        Wallet.user_id == trade.seller_id,
        Wallet.currency == trade.fiat_currency
    ).first()
    
    buyer_fiat_wallet = db.query(Wallet).filter(
        Wallet.user_id == trade.buyer_id,
        Wallet.currency == trade.fiat_currency
    ).first()
    
    # Buyer loses fiat, seller gains fiat
    if buyer_fiat_wallet:
        buyer_fiat_wallet.available_balance -= trade.total_fiat
    
    if seller_fiat_wallet:
        seller_fiat_wallet.available_balance += trade.total_fiat
    else:
        # Create wallet if doesn't exist
        seller_fiat_wallet = Wallet(
            user_id=trade.seller_id,
            currency=trade.fiat_currency,
            available_balance=trade.total_fiat,
            locked_balance=0
        )
        db.add(seller_fiat_wallet)
        db.flush()
    
    # Create transaction records for buyer (crypto received, fiat sent)
    buyer_crypto_transaction = Transaction(
        wallet_id=buyer_wallet.id,
        type=TransactionType.P2P_BUY,
        amount=trade.amount,
        currency=trade.currency,
        status="COMPLETED",
        reference_id=f"P2P_TRADE_{trade.id}",
        description=f"P2P Buy: {trade.amount} {trade.currency} from seller (Trade #{trade.id})"
    )
    db.add(buyer_crypto_transaction)
    
    if buyer_fiat_wallet:
        buyer_fiat_transaction = Transaction(
            wallet_id=buyer_fiat_wallet.id,
            type=TransactionType.P2P_BUY,
            amount=-trade.total_fiat,
            currency=trade.fiat_currency,
            status="COMPLETED",
            reference_id=f"P2P_TRADE_{trade.id}",
            description=f"P2P Payment: {trade.total_fiat} {trade.fiat_currency} to seller (Trade #{trade.id})"
        )
        db.add(buyer_fiat_transaction)
    
    # Create transaction records for seller (crypto sent, fiat received)
    if seller_wallet:
        seller_crypto_transaction = Transaction(
            wallet_id=seller_wallet.id,
            type=TransactionType.P2P_SELL,
            amount=-trade.amount,
            currency=trade.currency,
            status="COMPLETED",
            reference_id=f"P2P_TRADE_{trade.id}",
            description=f"P2P Sell: {trade.amount} {trade.currency} to buyer (Trade #{trade.id})"
        )
        db.add(seller_crypto_transaction)
    
    if seller_fiat_wallet:
        seller_fiat_transaction = Transaction(
            wallet_id=seller_fiat_wallet.id,
            type=TransactionType.P2P_SELL,
            amount=trade.total_fiat,
            currency=trade.fiat_currency,
            status="COMPLETED",
            reference_id=f"P2P_TRADE_{trade.id}",
            description=f"P2P Received: {trade.total_fiat} {trade.fiat_currency} from buyer (Trade #{trade.id})"
        )
        db.add(seller_fiat_transaction)
    
    # Update trade status
    trade.status = P2PTradeStatus.COMPLETED
    trade.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Trade completed successfully"}


@router.post("/trades/{trade_id}/cancel")
async def cancel_trade(
    trade_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel P2P trade"""
    trade = db.query(P2PTrade).filter(
        P2PTrade.id == trade_id,
        or_(
            P2PTrade.buyer_id == current_user.id,
            P2PTrade.seller_id == current_user.id
        )
    ).first()
    
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    if trade.status not in [P2PTradeStatus.PENDING, P2PTradeStatus.PAYMENT_SENT]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel completed or disputed trade"
        )
    
    # Refund escrow
    escrow = db.query(Escrow).filter(Escrow.id == trade.escrow_id).first()
    if escrow:
        escrow.status = "REFUNDED"
    
    # Unlock seller's funds
    seller_wallet = db.query(Wallet).filter(
        Wallet.user_id == trade.seller_id,
        Wallet.currency == trade.currency
    ).first()
    
    if seller_wallet:
        seller_wallet.locked_balance -= trade.amount
        seller_wallet.available_balance += trade.amount
    
    # Restore advertisement availability
    ad = db.query(P2PAdvertisement).filter(P2PAdvertisement.id == trade.advertisement_id).first()
    if ad:
        ad.available_amount += trade.amount
        if ad.available_amount > 0:
            ad.is_active = True
    
    trade.status = P2PTradeStatus.CANCELLED
    db.commit()
    
    return {"message": "Trade cancelled successfully"}


@router.get("/notifications", response_model=List[dict])
async def get_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications"""
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    notifications = query.order_by(desc(Notification.created_at)).limit(limit).all()
    
    return [
        {
            "id": n.id,
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "data": json.loads(n.data) if n.data else None,
            "is_read": n.is_read,
            "created_at": n.created_at
        }
        for n in notifications
    ]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.is_read = True
    db.commit()
    
    return {"message": "Notification marked as read"}


@router.post("/partial-match/accept/{ad_id}")
async def accept_partial_match(
    ad_id: int,
    match_ad_id: int,
    amount: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept a partial match notification"""
    
    user_ad = db.query(P2PAdvertisement).filter(
        P2PAdvertisement.id == ad_id,
        P2PAdvertisement.user_id == current_user.id
    ).first()
    
    match_ad = db.query(P2PAdvertisement).filter(P2PAdvertisement.id == match_ad_id).first()
    
    if not user_ad or not match_ad:
        raise HTTPException(status_code=404, detail="Advertisement not found")
    
    trade_amount = Decimal(str(amount))
    
    if trade_amount > user_ad.available_amount or trade_amount > match_ad.available_amount:
        raise HTTPException(status_code=400, detail="Invalid amount")
    
    # Create the trade
    trade = create_auto_trade(db, user_ad, match_ad, trade_amount, current_user.id)
    
    # Update amounts
    if user_ad.available_amount <= 0:
        user_ad.is_active = False
    if match_ad.available_amount <= 0:
        match_ad.is_active = False
    
    db.commit()
    
    return {"message": "Partial match accepted", "trade_id": trade.id}

