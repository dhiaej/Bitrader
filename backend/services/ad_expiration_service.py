"""
P2P Advertisement Expiration Service
Automatically expires advertisements after their payment_time_limit
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import and_
from sqlalchemy.orm import Session
import logging

from database import SessionLocal
from models import P2PAdvertisement, P2PTrade, Escrow, Wallet, P2PTradeStatus, Notification

logger = logging.getLogger(__name__)


class AdExpirationService:
    """Service to automatically expire old P2P advertisements"""
    
    def __init__(self):
        self.running = False
        self.task = None
    
    async def start(self):
        """Start the expiration checker"""
        if self.running:
            logger.warning("Ad expiration service already running")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._expiration_loop())
        logger.info("🕐 Ad expiration service started - checking every 60 seconds")
    
    async def stop(self):
        """Stop the expiration checker"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Ad expiration service stopped")
    
    async def _expiration_loop(self):
        """Main loop that checks for expired ads"""
        while self.running:
            try:
                await self._check_and_expire_ads()
                await asyncio.sleep(60)  # Check every 60 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ad expiration loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_expire_ads(self):
        """Check and expire old advertisements"""
        db = SessionLocal()
        try:
            # Get all active ads
            active_ads = db.query(P2PAdvertisement).filter(
                P2PAdvertisement.is_active == True
            ).all()
            
            if not active_ads:
                return
            
            now = datetime.utcnow()
            expired_count = 0
            cancelled_trades = 0
            
            for ad in active_ads:
                # Calculate expiration time
                expiry_time = ad.created_at + timedelta(minutes=ad.payment_time_limit)
                
                # Check if expired
                if now > expiry_time:
                    ad.is_active = False
                    expired_count += 1
                    
                    # Check for pending trades on this ad
                    pending_trades = db.query(P2PTrade).filter(
                        P2PTrade.advertisement_id == ad.id,
                        P2PTrade.status.in_([P2PTradeStatus.PENDING, P2PTradeStatus.PAYMENT_SENT])
                    ).all()
                    
                    # Cancel pending trades and refund escrow
                    for trade in pending_trades:
                        # Refund escrow
                        escrow = db.query(Escrow).filter(Escrow.id == trade.escrow_id).first()
                        if escrow and escrow.status == "LOCKED":
                            escrow.status = "REFUNDED"
                            
                            # Unlock seller's funds
                            seller_wallet = db.query(Wallet).filter(
                                Wallet.user_id == trade.seller_id,
                                Wallet.currency == trade.currency
                            ).first()
                            
                            if seller_wallet:
                                seller_wallet.locked_balance -= trade.amount
                                seller_wallet.available_balance += trade.amount
                        
                        # Restore ad availability
                        ad.available_amount += trade.amount
                        
                        # Update trade status
                        trade.status = P2PTradeStatus.CANCELLED
                        cancelled_trades += 1
                        
                        # Notify both parties
                        buyer_notification = Notification(
                            user_id=trade.buyer_id,
                            type="TRADE_CANCELLED",
                            title="Trade Cancelled - Ad Expired",
                            message=f"Trade #{trade.id} was cancelled because the advertisement expired.",
                            data='{"reason": "ad_expired"}'
                        )
                        seller_notification = Notification(
                            user_id=trade.seller_id,
                            type="TRADE_CANCELLED",
                            title="Trade Cancelled - Ad Expired",
                            message=f"Trade #{trade.id} was cancelled because your advertisement expired. Funds have been unlocked.",
                            data='{"reason": "ad_expired"}'
                        )
                        db.add(buyer_notification)
                        db.add(seller_notification)
                    
                    logger.info(
                        f"⏰ Expired advertisement #{ad.id}: "
                        f"{ad.ad_type.value} {ad.available_amount} {ad.currency} "
                        f"(created {ad.created_at}, limit {ad.payment_time_limit} min)"
                        + (f" - Cancelled {len(pending_trades)} pending trades" if pending_trades else "")
                    )
            
            if expired_count > 0:
                db.commit()
                logger.info(
                    f"✅ Expired {expired_count} advertisements" +
                    (f" and cancelled {cancelled_trades} pending trades" if cancelled_trades > 0 else "")
                )
                
        except Exception as e:
            logger.error(f"Error checking expired ads: {e}")
            db.rollback()
        finally:
            db.close()


# Singleton instance
ad_expiration_service = AdExpirationService()

