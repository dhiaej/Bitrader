"""
Wallet Router - Balance management, transactions, deposits, withdrawals
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from decimal import Decimal

from database import get_db
from models import User, Wallet, Transaction, TransactionType
from schemas import WalletResponse, TransactionResponse, TransferRequest, WalletBalanceUpdate, DepositRequest, WithdrawRequest
from utils.auth import get_current_user

router = APIRouter()


@router.get("/balances", response_model=List[WalletResponse])
async def get_wallets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all user wallets with balances"""
    wallets = db.query(Wallet).filter(Wallet.user_id == current_user.id).all()
    return wallets


@router.get("/balance/{currency}", response_model=WalletResponse)
async def get_wallet_balance(
    currency: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific currency wallet balance"""
    wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.currency == currency.upper()
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet for {currency} not found"
        )
    
    return wallet


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(
    currency: str = None,
    transaction_type: str = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history with optional filters"""
    
    # Get user's wallets
    wallet_ids = db.query(Wallet.id).filter(Wallet.user_id == current_user.id).all()
    wallet_ids = [w[0] for w in wallet_ids]
    
    query = db.query(Transaction).filter(Transaction.wallet_id.in_(wallet_ids))
    
    if currency:
        query = query.filter(Transaction.currency == currency.upper())
    
    if transaction_type:
        query = query.filter(Transaction.type == transaction_type.upper())
    
    transactions = query.order_by(desc(Transaction.created_at)).offset(offset).limit(limit).all()
    
    return transactions


@router.post("/deposit", response_model=TransactionResponse)
async def deposit_funds(
    request: DepositRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deposit funds (virtual - for game purposes)"""
    
    wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.currency == request.currency.upper()
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet for {request.currency} not found"
        )
    
    # Update balance
    wallet.available_balance += Decimal(str(request.amount))
    
    # Create transaction record
    transaction = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.DEPOSIT,
        amount=Decimal(str(request.amount)),
        currency=request.currency.upper(),
        status="COMPLETED",
        description=f"Virtual deposit of {request.amount} {request.currency}"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/withdraw", response_model=TransactionResponse)
async def withdraw_funds(
    request: WithdrawRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Withdraw funds (virtual - for game purposes)"""
    
    wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.currency == request.currency.upper()
    ).first()
    
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Wallet for {request.currency} not found"
        )
    
    if wallet.available_balance < Decimal(str(request.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Update balance
    wallet.available_balance -= Decimal(str(request.amount))
    
    # Create transaction record
    address_info = f" to {request.address}" if request.address else ""
    transaction = Transaction(
        wallet_id=wallet.id,
        type=TransactionType.WITHDRAWAL,
        amount=Decimal(str(request.amount)),
        currency=request.currency.upper(),
        status="COMPLETED",
        description=f"Virtual withdrawal of {request.amount} {request.currency}{address_info}"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(transaction)
    
    return transaction


@router.post("/transfer", response_model=dict)
async def transfer_funds(
    transfer_data: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfer funds to another user"""
    
    if transfer_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be positive"
        )
    
    # Get recipient user
    recipient = db.query(User).filter(User.username == transfer_data.recipient_username).first()
    if not recipient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient user not found"
        )
    
    if recipient.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to yourself"
        )
    
    # Get sender wallet
    sender_wallet = db.query(Wallet).filter(
        Wallet.user_id == current_user.id,
        Wallet.currency == transfer_data.currency.upper()
    ).first()
    
    if not sender_wallet or sender_wallet.available_balance < Decimal(str(transfer_data.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient balance"
        )
    
    # Get recipient wallet
    recipient_wallet = db.query(Wallet).filter(
        Wallet.user_id == recipient.id,
        Wallet.currency == transfer_data.currency.upper()
    ).first()
    
    if not recipient_wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient wallet for {transfer_data.currency} not found"
        )
    
    # Perform transfer
    sender_wallet.available_balance -= Decimal(str(transfer_data.amount))
    recipient_wallet.available_balance += Decimal(str(transfer_data.amount))
    
    # Create transaction records
    sender_tx = Transaction(
        wallet_id=sender_wallet.id,
        type=TransactionType.TRANSFER,
        amount=-Decimal(str(transfer_data.amount)),
        currency=transfer_data.currency.upper(),
        status="COMPLETED",
        description=f"Transfer to {recipient.username}"
    )
    
    recipient_tx = Transaction(
        wallet_id=recipient_wallet.id,
        type=TransactionType.TRANSFER,
        amount=Decimal(str(transfer_data.amount)),
        currency=transfer_data.currency.upper(),
        status="COMPLETED",
        description=f"Transfer from {current_user.username}"
    )
    
    db.add(sender_tx)
    db.add(recipient_tx)
    db.commit()
    
    return {
        "message": "Transfer successful",
        "amount": transfer_data.amount,
        "currency": transfer_data.currency,
        "recipient": recipient.username
    }
