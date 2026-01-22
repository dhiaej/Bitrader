"""
Dispute Router - P2P Trade Dispute Management
Handles dispute filing, evidence submission, and admin resolution
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Dispute, P2PTrade, User, P2PTradeStatus, DisputeStatus, Escrow
from schemas import (
    DisputeCreate, 
    DisputeResponse, 
    DisputeListResponse,
    DisputeAddEvidence,
    DisputeUpdate,
    DisputeResolve
)
from utils.auth import get_current_user, get_current_admin

router = APIRouter()


def _serialize_dispute(dispute: Dispute, db: Session) -> DisputeResponse:
    """Helper to serialize dispute with related data"""
    # Get trade details
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    
    # Get usernames
    filed_by_user = db.query(User).filter(User.id == dispute.filed_by).first()
    resolved_by_user = None
    if dispute.resolved_by:
        resolved_by_user = db.query(User).filter(User.id == dispute.resolved_by).first()
    
    buyer_user = None
    seller_user = None
    if trade:
        buyer_user = db.query(User).filter(User.id == trade.buyer_id).first()
        seller_user = db.query(User).filter(User.id == trade.seller_id).first()
    
    return DisputeResponse(
        id=dispute.id,
        trade_id=dispute.trade_id,
        filed_by=dispute.filed_by,
        filed_by_username=filed_by_user.username if filed_by_user else None,
        reason=dispute.reason,
        evidence=dispute.evidence,
        status=dispute.status.value if dispute.status else "OPEN",
        resolution=dispute.resolution,
        resolved_by=dispute.resolved_by,
        resolved_by_username=resolved_by_user.username if resolved_by_user else None,
        created_at=dispute.created_at,
        resolved_at=dispute.resolved_at,
        trade_amount=float(trade.amount) if trade else None,
        trade_currency=trade.currency if trade else None,
        buyer_id=trade.buyer_id if trade else None,
        buyer_username=buyer_user.username if buyer_user else None,
        seller_id=trade.seller_id if trade else None,
        seller_username=seller_user.username if seller_user else None
    )


@router.post("/", response_model=DisputeResponse, status_code=status.HTTP_201_CREATED)
async def create_dispute(
    dispute_data: DisputeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    File a dispute on a P2P trade.
    Only the buyer or seller can file a dispute on their trade.
    """
    # Verify trade exists
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute_data.trade_id).first()
    if not trade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trade not found"
        )
    
    # Verify user is part of the trade
    if trade.buyer_id != current_user.id and trade.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only file disputes on your own trades"
        )
    
    # Check if trade can be disputed
    if trade.status in [P2PTradeStatus.COMPLETED, P2PTradeStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot file dispute on {trade.status.value} trade"
        )
    
    # Check if dispute already exists
    existing_dispute = db.query(Dispute).filter(Dispute.trade_id == dispute_data.trade_id).first()
    if existing_dispute:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dispute already exists for this trade"
        )
    
    # Create dispute
    new_dispute = Dispute(
        trade_id=dispute_data.trade_id,
        filed_by=current_user.id,
        reason=dispute_data.reason,
        evidence=dispute_data.evidence,
        status=DisputeStatus.OPEN
    )
    
    db.add(new_dispute)
    
    # Update trade status to DISPUTED
    trade.status = P2PTradeStatus.DISPUTED
    
    db.commit()
    db.refresh(new_dispute)
    
    return _serialize_dispute(new_dispute, db)


@router.get("/my-disputes", response_model=DisputeListResponse)
async def get_my_disputes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all disputes filed by or involving the current user"""
    # Get trades where user is buyer or seller
    user_trades = db.query(P2PTrade).filter(
        (P2PTrade.buyer_id == current_user.id) | (P2PTrade.seller_id == current_user.id)
    ).all()
    
    trade_ids = [trade.id for trade in user_trades]
    
    # Get disputes for these trades
    disputes = db.query(Dispute).filter(
        Dispute.trade_id.in_(trade_ids)
    ).order_by(desc(Dispute.created_at)).all()
    
    return DisputeListResponse(
        total=len(disputes),
        disputes=[_serialize_dispute(d, db) for d in disputes]
    )


@router.get("/{dispute_id}", response_model=DisputeResponse)
async def get_dispute(
    dispute_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get details of a specific dispute"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Verify user has access (is part of trade or is admin)
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    if not current_user.is_admin:
        if not trade or (trade.buyer_id != current_user.id and trade.seller_id != current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this dispute"
            )
    
    return _serialize_dispute(dispute, db)


@router.post("/{dispute_id}/evidence", response_model=DisputeResponse)
async def add_evidence(
    dispute_id: int,
    evidence_data: DisputeAddEvidence,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add additional evidence to a dispute"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Verify user is part of the trade
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    if not trade or (trade.buyer_id != current_user.id and trade.seller_id != current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only add evidence to your own disputes"
        )
    
    # Can't add evidence to resolved disputes
    if dispute.status == DisputeStatus.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot add evidence to resolved dispute"
        )
    
    # Append evidence (stored as JSON array string)
    import json
    evidence_list = []
    if dispute.evidence:
        try:
            evidence_list = json.loads(dispute.evidence)
        except:
            evidence_list = [dispute.evidence]
    
    evidence_list.append({
        "user_id": current_user.id,
        "username": current_user.username,
        "content": evidence_data.evidence,
        "timestamp": datetime.utcnow().isoformat()
    })
    
    dispute.evidence = json.dumps(evidence_list)
    
    # Update status to IN_REVIEW if still OPEN
    if dispute.status == DisputeStatus.OPEN:
        dispute.status = DisputeStatus.IN_REVIEW
    
    db.commit()
    db.refresh(dispute)
    
    return _serialize_dispute(dispute, db)


@router.put("/{dispute_id}", response_model=DisputeResponse)
async def update_dispute(
    dispute_id: int,
    update_data: DisputeUpdate,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update dispute status (admin only)"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Update status
    if update_data.status:
        try:
            dispute.status = DisputeStatus(update_data.status.upper())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status"
            )
    
    # Update resolution
    if update_data.resolution:
        dispute.resolution = update_data.resolution
    
    db.commit()
    db.refresh(dispute)
    
    return _serialize_dispute(dispute, db)


@router.post("/{dispute_id}/resolve", response_model=DisputeResponse)
async def resolve_dispute(
    dispute_id: int,
    resolution_data: DisputeResolve,
    admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Resolve a dispute and handle fund distribution (admin only)
    - Release funds to buyer (refund) or seller based on decision
    - Update trade status
    - Update reputation scores
    """
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
    if resolution_data.refund_to_buyer:
        # Buyer wins - refund buyer (crypto goes back to seller, fiat returned to buyer)
        trade.status = P2PTradeStatus.CANCELLED
        if escrow:
            escrow.status = "REFUNDED"
            escrow.released_at = datetime.utcnow()
        
    elif resolution_data.release_to_seller:
        # Seller wins - release crypto to buyer (trade completes normally)
        trade.status = P2PTradeStatus.COMPLETED
        trade.completed_at = datetime.utcnow()
        if escrow:
            escrow.status = "RELEASED"
            escrow.released_at = datetime.utcnow()
    
    # Update dispute
    dispute.status = DisputeStatus.RESOLVED
    dispute.resolution = resolution_data.resolution
    dispute.resolved_by = admin_user.id
    dispute.resolved_at = datetime.utcnow()
    
    db.commit()
    db.refresh(dispute)
    
    return _serialize_dispute(dispute, db)


@router.delete("/{dispute_id}")
async def cancel_dispute(
    dispute_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a dispute (only by the user who filed it, and only if OPEN)"""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dispute not found"
        )
    
    # Only the filer can cancel
    if dispute.filed_by != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only cancel your own disputes"
        )
    
    # Can only cancel OPEN disputes
    if dispute.status != DisputeStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only cancel disputes that are still OPEN"
        )
    
    # Update trade status back to original
    trade = db.query(P2PTrade).filter(P2PTrade.id == dispute.trade_id).first()
    if trade and trade.status == P2PTradeStatus.DISPUTED:
        # Determine appropriate status based on trade state
        if trade.payment_confirmed:
            trade.status = P2PTradeStatus.PAYMENT_CONFIRMED
        elif trade.buyer_id:
            trade.status = P2PTradeStatus.PENDING
        
    db.delete(dispute)
    db.commit()
    
    return {"message": "Dispute cancelled successfully"}
