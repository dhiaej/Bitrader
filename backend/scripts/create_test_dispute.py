"""
Create a dispute directly in the database for testing
"""
from database import SessionLocal
from models import Dispute, DisputeStatus, P2PTrade
from datetime import datetime

db = SessionLocal()

try:
    # Check if dispute already exists on trade 1
    existing = db.query(Dispute).filter(Dispute.trade_id == 1).first()
    
    if existing:
        print(f'⚠️ Dispute already exists on Trade ID 1')
        print(f'   Dispute ID: {existing.id}')
        print(f'   Status: {existing.status.value}')
    else:
        # Create dispute
        dispute = Dispute(
            trade_id=1,
            filed_by=8,  # alice_trader (buyer)
            reason="I sent the payment via bank transfer 2 days ago but the seller has not released the Bitcoin. I have payment proof.",
            evidence='{"payment_receipt": "TXN123456", "amount": "$992.43"}',
            status=DisputeStatus.OPEN
        )
        db.add(dispute)
        
        # Update trade status
        trade = db.query(P2PTrade).filter(P2PTrade.id == 1).first()
        if trade:
            from models import P2PTradeStatus
            trade.status = P2PTradeStatus.DISPUTED
        
        db.commit()
        db.refresh(dispute)
        
        print('✅ Dispute created successfully!')
        print(f'   Dispute ID: {dispute.id}')
        print(f'   Trade ID: {dispute.trade_id}')
        print(f'   Filed by: User ID {dispute.filed_by}')
        print(f'   Status: {dispute.status.value}')
        print(f'')
        print('👉 View it in:')
        print(f'   - Admin Dashboard: http://localhost:4200/admin (Disputes tab)')
        print(f'   - User View: http://localhost:4200/disputes')
        
except Exception as e:
    print(f'❌ Error: {e}')
    db.rollback()
finally:
    db.close()
