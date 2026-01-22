"""
Order Book Router - Trading orders, order matching, market depth
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from database import get_db
from models import User, OrderBookOrder, Trade, OrderType, OrderStatus, OrderBookOrderType, Wallet, Transaction, TransactionType
from schemas import OrderCreate, OrderResponse, OrderBookSnapshot, TradeResponse
from utils.auth import get_current_user
from config import settings

router = APIRouter()


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new order and attempt to match it"""
    
    # Validate order
    if order_data.order_subtype == "LIMIT" and order_data.price is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price required for limit orders"
        )
    
    # Validate price (must be positive)
    if order_data.price is not None and order_data.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Price must be greater than 0"
        )
    
    # Validate quantity (must be positive)
    if order_data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity must be greater than 0"
        )
    
    # Parse instrument (e.g., BTC/USD -> BTC and USD)
    try:
        base_currency, quote_currency = order_data.instrument.split("/")
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid instrument format. Use format: BTC/USD"
        )
    
    # Check wallet balance
    if order_data.order_type == "BUY":
        # Need quote currency (USD) to buy
        required_amount = order_data.quantity * (order_data.price or 0)
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.currency == quote_currency
        ).first()
        
        if not wallet or wallet.available_balance < Decimal(str(required_amount)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient {quote_currency} balance"
            )
        
        # Lock funds
        wallet.available_balance -= Decimal(str(required_amount))
        wallet.locked_balance += Decimal(str(required_amount))
        
    else:  # SELL
        # Need base currency (BTC) to sell
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.currency == base_currency
        ).first()
        
        if not wallet or wallet.available_balance < Decimal(str(order_data.quantity)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient {base_currency} balance"
            )
        
        # Lock funds
        wallet.available_balance -= Decimal(str(order_data.quantity))
        wallet.locked_balance += Decimal(str(order_data.quantity))
    
    # Create order
    new_order = OrderBookOrder(
        user_id=current_user.id,
        instrument=order_data.instrument,
        order_type=OrderType(order_data.order_type),
        order_subtype=OrderBookOrderType(order_data.order_subtype),
        price=Decimal(str(order_data.price)) if order_data.price else None,
        quantity=Decimal(str(order_data.quantity)),
        remaining_quantity=Decimal(str(order_data.quantity)),
        status=OrderStatus.PENDING
    )
    
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    
    # Attempt to match order
    try:
        match_order(new_order.id, db)
    except Exception as e:
        print(f"Order matching error: {e}")
    
    return new_order


@router.get("/orders", response_model=List[OrderResponse])
async def get_user_orders(
    instrument: Optional[str] = None,
    status_filter: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's orders"""
    query = db.query(OrderBookOrder).filter(OrderBookOrder.user_id == current_user.id)
    
    if instrument:
        query = query.filter(OrderBookOrder.instrument == instrument)
    
    if status_filter:
        query = query.filter(OrderBookOrder.status == status_filter.upper())
    
    orders = query.order_by(desc(OrderBookOrder.created_at)).limit(limit).all()
    return orders


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific order details"""
    order = db.query(OrderBookOrder).filter(
        OrderBookOrder.id == order_id,
        OrderBookOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel an order"""
    order = db.query(OrderBookOrder).filter(
        OrderBookOrder.id == order_id,
        OrderBookOrder.user_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    if order.status not in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel pending or partially filled orders"
        )
    
    # Unlock funds
    base_currency, quote_currency = order.instrument.split("/")
    
    if order.order_type == OrderType.BUY:
        locked_amount = order.remaining_quantity * order.price
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.currency == quote_currency
        ).first()
        
        if wallet:
            wallet.locked_balance -= locked_amount
            wallet.available_balance += locked_amount
    else:
        wallet = db.query(Wallet).filter(
            Wallet.user_id == current_user.id,
            Wallet.currency == base_currency
        ).first()
        
        if wallet:
            wallet.locked_balance -= order.remaining_quantity
            wallet.available_balance += order.remaining_quantity
    
    order.status = OrderStatus.CANCELLED
    db.commit()
    
    return {"message": "Order cancelled successfully"}


@router.get("", response_model=OrderBookSnapshot)
async def get_order_book(
    instrument: str,
    depth: int = 20,
    db: Session = Depends(get_db)
):
    """Get order book snapshot for an instrument"""
    try:
        # Get buy orders (bids) - highest price first (only limit orders with prices)
        buy_orders = db.query(OrderBookOrder).filter(
            OrderBookOrder.instrument == instrument,
            OrderBookOrder.order_type == OrderType.BUY,
            OrderBookOrder.status.in_([OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]),
            OrderBookOrder.price.isnot(None)  # Only orders with prices
        ).order_by(desc(OrderBookOrder.price), OrderBookOrder.created_at).limit(depth).all()
        
        # Get sell orders (asks) - lowest price first (only limit orders with prices)
        sell_orders = db.query(OrderBookOrder).filter(
            OrderBookOrder.instrument == instrument,
            OrderBookOrder.order_type == OrderType.SELL,
            OrderBookOrder.status.in_([OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]),
            OrderBookOrder.price.isnot(None)  # Only orders with prices
        ).order_by(OrderBookOrder.price, OrderBookOrder.created_at).limit(depth).all()
        
        # Aggregate by price
        bids = {}
        for order in buy_orders:
            if order.price is not None:
                price = float(order.price)
                if price not in bids:
                    bids[price] = {"price": price, "quantity": 0, "count": 0}
                bids[price]["quantity"] += float(order.remaining_quantity)
                bids[price]["count"] += 1
        
        asks = {}
        for order in sell_orders:
            if order.price is not None:
                price = float(order.price)
                if price not in asks:
                    asks[price] = {"price": price, "quantity": 0, "count": 0}
                asks[price]["quantity"] += float(order.remaining_quantity)
                asks[price]["count"] += 1
        
        # Get last trade price
        last_trade = db.query(Trade).filter(Trade.instrument == instrument).order_by(desc(Trade.created_at)).first()
        last_price = float(last_trade.price) if last_trade and last_trade.price else None
        
        return {
            "instrument": instrument,
            "bids": sorted(bids.values(), key=lambda x: x["price"], reverse=True),
            "asks": sorted(asks.values(), key=lambda x: x["price"]),
            "last_price": last_price,
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        # Log the error and return empty orderbook instead of crashing
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error fetching orderbook for {instrument}: {e}", exc_info=True)
        return {
            "instrument": instrument,
            "bids": [],
            "asks": [],
            "last_price": None,
            "timestamp": datetime.utcnow()
        }


@router.get("/trades", response_model=List[TradeResponse])
async def get_trades(
    instrument: Optional[str] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's trade history"""
    query = db.query(Trade).filter(
        or_(
            Trade.buyer_id == current_user.id,
            Trade.seller_id == current_user.id
        )
    )
    
    if instrument:
        query = query.filter(Trade.instrument == instrument)
    
    trades = query.order_by(desc(Trade.created_at)).limit(limit).all()
    return trades


# ============= ORDER MATCHING ENGINE =============
def match_order(order_id: int, db: Session):
    """
    Match an order with existing orders in the order book
    Implements price-time priority matching
    """
    from datetime import datetime
    
    order = db.query(OrderBookOrder).filter(OrderBookOrder.id == order_id).first()
    if not order or order.remaining_quantity <= 0:
        return
    
    # Get matching orders
    if order.order_type == OrderType.BUY:
        # Match with sell orders at or below buy price
        matching_orders = db.query(OrderBookOrder).filter(
            OrderBookOrder.instrument == order.instrument,
            OrderBookOrder.order_type == OrderType.SELL,
            OrderBookOrder.status.in_([OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]),
            OrderBookOrder.id != order.id
        )
        
        if order.price:  # Limit order
            matching_orders = matching_orders.filter(OrderBookOrder.price <= order.price)
        
        matching_orders = matching_orders.order_by(OrderBookOrder.price, OrderBookOrder.created_at).all()
        
    else:  # SELL
        # Match with buy orders at or above sell price
        matching_orders = db.query(OrderBookOrder).filter(
            OrderBookOrder.instrument == order.instrument,
            OrderBookOrder.order_type == OrderType.BUY,
            OrderBookOrder.status.in_([OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]),
            OrderBookOrder.id != order.id
        )
        
        if order.price:  # Limit order
            matching_orders = matching_orders.filter(OrderBookOrder.price >= order.price)
        
        matching_orders = matching_orders.order_by(desc(OrderBookOrder.price), OrderBookOrder.created_at).all()
    
    # Execute matches
    for matching_order in matching_orders:
        if order.remaining_quantity <= 0:
            break
        
        # Determine trade quantity and price
        trade_quantity = min(order.remaining_quantity, matching_order.remaining_quantity)
        trade_price = matching_order.price  # Existing order price
        trade_amount = trade_quantity * trade_price
        
        # Calculate fee
        fee = trade_amount * Decimal(str(settings.TRADING_FEE_PERCENTAGE / 100))
        
        # Update order quantities
        order.remaining_quantity -= trade_quantity
        matching_order.remaining_quantity -= trade_quantity
        
        # Update order statuses
        if order.remaining_quantity == 0:
            order.status = OrderStatus.FILLED
        elif order.remaining_quantity < order.quantity:
            order.status = OrderStatus.PARTIALLY_FILLED
        
        if matching_order.remaining_quantity == 0:
            matching_order.status = OrderStatus.FILLED
        elif matching_order.remaining_quantity < matching_order.quantity:
            matching_order.status = OrderStatus.PARTIALLY_FILLED
        
        # Create trade record
        base_currency, quote_currency = order.instrument.split("/")
        buyer_id = order.user_id if order.order_type == OrderType.BUY else matching_order.user_id
        seller_id = matching_order.user_id if order.order_type == OrderType.BUY else order.user_id
        
        trade = Trade(
            order_id=order.id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            instrument=order.instrument,
            price=trade_price,
            quantity=trade_quantity,
            total_amount=trade_amount,
            fee=fee
        )
        db.add(trade)
        
        # Update wallets
        execute_trade_settlement(buyer_id, seller_id, base_currency, quote_currency, trade_quantity, trade_amount, fee, db)
        
        db.commit()


def execute_trade_settlement(buyer_id: int, seller_id: int, base_currency: str, quote_currency: str, 
                            quantity: Decimal, amount: Decimal, fee: Decimal, db: Session):
    """Execute wallet updates after trade and create transaction records"""
    
    # Buyer: unlock quote currency, receive base currency
    buyer_quote_wallet = db.query(Wallet).filter(
        Wallet.user_id == buyer_id,
        Wallet.currency == quote_currency
    ).first()
    
    buyer_base_wallet = db.query(Wallet).filter(
        Wallet.user_id == buyer_id,
        Wallet.currency == base_currency
    ).first()
    
    if buyer_quote_wallet:
        buyer_quote_wallet.locked_balance -= amount
        # Create transaction record for quote currency spent
        tx = Transaction(
            wallet_id=buyer_quote_wallet.id,
            type=TransactionType.TRADE,
            amount=-amount,
            currency=quote_currency,
            status="COMPLETED",
            description=f"Buy {quantity} {base_currency} at {amount/quantity} {quote_currency}"
        )
        db.add(tx)
    
    if buyer_base_wallet:
        received_quantity = quantity - (quantity * fee / amount)
        buyer_base_wallet.available_balance += received_quantity
        # Create transaction record for base currency received
        tx = Transaction(
            wallet_id=buyer_base_wallet.id,
            type=TransactionType.TRADE,
            amount=received_quantity,
            currency=base_currency,
            status="COMPLETED",
            description=f"Received {received_quantity} {base_currency} (fee: {quantity * fee / amount})"
        )
        db.add(tx)
    
    # Seller: unlock base currency, receive quote currency
    seller_base_wallet = db.query(Wallet).filter(
        Wallet.user_id == seller_id,
        Wallet.currency == base_currency
    ).first()
    
    seller_quote_wallet = db.query(Wallet).filter(
        Wallet.user_id == seller_id,
        Wallet.currency == quote_currency
    ).first()
    
    if seller_base_wallet:
        seller_base_wallet.locked_balance -= quantity
        # Create transaction record for base currency sold
        tx = Transaction(
            wallet_id=seller_base_wallet.id,
            type=TransactionType.TRADE,
            amount=-quantity,
            currency=base_currency,
            status="COMPLETED",
            description=f"Sell {quantity} {base_currency} at {amount/quantity} {quote_currency}"
        )
        db.add(tx)
    
    if seller_quote_wallet:
        received_amount = amount - fee
        seller_quote_wallet.available_balance += received_amount
        # Create transaction record for quote currency received
        tx = Transaction(
            wallet_id=seller_quote_wallet.id,
            type=TransactionType.TRADE,
            amount=received_amount,
            currency=quote_currency,
            status="COMPLETED",
            description=f"Received {received_amount} {quote_currency} from sale (fee: {fee})"
        )
        db.add(tx)
