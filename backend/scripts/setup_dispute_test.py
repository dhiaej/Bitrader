"""
Setup Test Data for Dispute System
Creates necessary test data including users, wallets, P2P trades with PAYMENT_SENT status
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    User, Wallet, P2PAdvertisement, P2PTrade, Escrow,
    OrderType, P2PTradeStatus
)
from decimal import Decimal
import json
from datetime import datetime, timedelta

def setup_dispute_test_data():
    """Create test data for dispute functionality testing"""
    
    print("🔧 Setting up Dispute Test Data...")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Step 1: Create or get test users
        print("\n📝 Step 1: Creating/Getting Test Users...")
        
        # Create buyer user
        buyer = db.query(User).filter(User.username == "buyer_test").first()
        if not buyer:
            buyer = User(
                username="buyer_test",
                email="buyer@test.com",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYZBhZqWJmm8lRe",  # "password123"
                full_name="Test Buyer",
                is_active=True,
                is_verified=True
            )
            db.add(buyer)
            db.flush()
            print(f"   ✅ Created buyer: {buyer.username} (ID: {buyer.id})")
        else:
            print(f"   ℹ️  Using existing buyer: {buyer.username} (ID: {buyer.id})")
        
        # Create seller user
        seller = db.query(User).filter(User.username == "seller_test").first()
        if not seller:
            seller = User(
                username="seller_test",
                email="seller@test.com",
                hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewYZBhZqWJmm8lRe",  # "password123"
                full_name="Test Seller",
                is_active=True,
                is_verified=True
            )
            db.add(seller)
            db.flush()
            print(f"   ✅ Created seller: {seller.username} (ID: {seller.id})")
        else:
            print(f"   ℹ️  Using existing seller: {seller.username} (ID: {seller.id})")
        
        db.commit()
        
        # Step 2: Ensure users have wallets with funds
        print("\n💰 Step 2: Setting Up Wallets...")
        
        # Buyer wallet (needs crypto for buying)
        buyer_btc_wallet = db.query(Wallet).filter(
            Wallet.user_id == buyer.id,
            Wallet.currency == "BTC"
        ).first()
        
        if not buyer_btc_wallet:
            buyer_btc_wallet = Wallet(
                user_id=buyer.id,
                currency="BTC",
                available_balance=Decimal("0.5")
            )
            db.add(buyer_btc_wallet)
            print(f"   ✅ Created BTC wallet for buyer with 0.5 BTC")
        else:
            buyer_btc_wallet.available_balance = max(buyer_btc_wallet.available_balance, Decimal("0.5"))
            print(f"   ℹ️  Updated buyer BTC wallet balance to {buyer_btc_wallet.available_balance}")
        
        # Seller wallet (has crypto to sell)
        seller_btc_wallet = db.query(Wallet).filter(
            Wallet.user_id == seller.id,
            Wallet.currency == "BTC"
        ).first()
        
        if not seller_btc_wallet:
            seller_btc_wallet = Wallet(
                user_id=seller.id,
                currency="BTC",
                available_balance=Decimal("2.0")
            )
            db.add(seller_btc_wallet)
            print(f"   ✅ Created BTC wallet for seller with 2.0 BTC")
        else:
            seller_btc_wallet.available_balance = max(seller_btc_wallet.available_balance, Decimal("2.0"))
            print(f"   ℹ️  Updated seller BTC wallet balance to {seller_btc_wallet.available_balance}")
        
        db.commit()
        
        # Step 3: Create P2P Advertisement
        print("\n📢 Step 3: Creating P2P Advertisement...")
        
        ad = db.query(P2PAdvertisement).filter(
            P2PAdvertisement.user_id == seller.id,
            P2PAdvertisement.ad_type == OrderType.SELL,
            P2PAdvertisement.currency == "BTC"
        ).first()
        
        if not ad:
            ad = P2PAdvertisement(
                user_id=seller.id,
                ad_type=OrderType.SELL,
                currency="BTC",
                fiat_currency="USD",
                price=Decimal("45000.00"),
                min_limit=Decimal("100"),
                max_limit=Decimal("10000"),
                available_amount=Decimal("1.0"),
                payment_methods=json.dumps(["Bank Transfer", "PayPal"]),
                payment_time_limit=30,
                terms_conditions="Fast and reliable trader. Will dispute if payment not received!"
            )
            db.add(ad)
            db.flush()
            print(f"   ✅ Created P2P ad (ID: {ad.id}) - Selling BTC at $45,000")
        else:
            print(f"   ℹ️  Using existing ad (ID: {ad.id})")
        
        db.commit()
        
        # Step 4: Create P2P Trade with PAYMENT_SENT status
        print("\n🔄 Step 4: Creating P2P Trade (PAYMENT_SENT Status)...")
        
        trade_amount = Decimal("0.1")  # 0.1 BTC
        fiat_amount = Decimal("4500.00")  # $4,500 USD
        
        # Check if trade already exists
        existing_trade = db.query(P2PTrade).filter(
            P2PTrade.buyer_id == buyer.id,
            P2PTrade.seller_id == seller.id,
            P2PTrade.status == P2PTradeStatus.PAYMENT_SENT
        ).first()
        
        if existing_trade:
            trade = existing_trade
            print(f"   ℹ️  Using existing trade (ID: {trade.id}) with PAYMENT_SENT status")
        else:
            trade = P2PTrade(
                advertisement_id=ad.id,
                buyer_id=buyer.id,
                seller_id=seller.id,
                amount=trade_amount,
                currency="BTC",
                fiat_currency="USD",
                price=ad.price,
                total_fiat=fiat_amount,
                payment_method="Bank Transfer",
                status=P2PTradeStatus.PAYMENT_SENT,
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
            db.add(trade)
            db.flush()
            print(f"   ✅ Created trade (ID: {trade.id})")
            print(f"      Amount: {trade_amount} BTC")
            print(f"      Total: ${fiat_amount} USD")
            print(f"      Status: PAYMENT_SENT")
            print(f"      Payment Method: Bank Transfer")
        
        db.commit()
        
        # Step 5: Create Escrow (funds locked)
        print("\n🔒 Step 5: Creating Escrow...")
        
        escrow = db.query(Escrow).filter(Escrow.trade_id == trade.id).first()
        
        if not escrow:
            escrow = Escrow(
                amount=trade_amount,
                currency="BTC",
                status="LOCKED",
                locked_at=datetime.utcnow() - timedelta(hours=2)
            )
            db.add(escrow)
            db.flush()
            print(f"   ✅ Created escrow (ID: {escrow.id})")
            print(f"      Amount: {trade_amount} BTC")
            print(f"      Status: LOCKED")
        else:
            print(f"   ℹ️  Using existing escrow (ID: {escrow.id})")
        
        db.commit()
        
        # Step 6: Create another trade for testing
        print("\n🔄 Step 6: Creating Second P2P Trade (for variety)...")
        
        trade2 = db.query(P2PTrade).filter(
            P2PTrade.buyer_id == seller.id,  # Seller is now buyer
            P2PTrade.seller_id == buyer.id,  # Buyer is now seller
            P2PTrade.status == P2PTradeStatus.PAYMENT_SENT
        ).first()
        
        if not trade2:
            # Get or create ad for buyer (now selling)
            ad2 = P2PAdvertisement(
                user_id=buyer.id,
                ad_type=OrderType.SELL,
                currency="BTC",
                fiat_currency="USD",
                price=Decimal("44800.00"),
                min_limit=Decimal("50"),
                max_limit=Decimal("5000"),
                available_amount=Decimal("0.3"),
                payment_methods=json.dumps(["PayPal", "Wise"]),
                payment_time_limit=30,
                terms_conditions="Quick release after payment confirmation."
            )
            db.add(ad2)
            db.flush()
            
            trade2 = P2PTrade(
                advertisement_id=ad2.id,
                buyer_id=seller.id,
                seller_id=buyer.id,
                amount=Decimal("0.05"),
                currency="BTC",
                fiat_currency="USD",
                price=ad2.price,
                total_fiat=Decimal("2240.00"),
                payment_method="PayPal",
                status=P2PTradeStatus.PAYMENT_SENT,
                created_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.add(trade2)
            db.flush()
            
            escrow2 = Escrow(
                amount=Decimal("0.05"),
                currency="BTC",
                status="LOCKED",
                locked_at=datetime.utcnow() - timedelta(hours=1)
            )
            db.add(escrow2)
            
            print(f"   ✅ Created second trade (ID: {trade2.id})")
            print(f"      Amount: 0.05 BTC")
            print(f"      Total: $2,240 USD")
        else:
            print(f"   ℹ️  Second trade already exists (ID: {trade2.id})")
        
        db.commit()
        
        # Step 7: Summary
        print("\n" + "=" * 70)
        print("✅ SETUP COMPLETE!")
        print("=" * 70)
        print("\n📋 Test Data Summary:")
        print(f"\n👥 Users Created:")
        print(f"   • Buyer:  username='{buyer.username}', password='password123', ID={buyer.id}")
        print(f"   • Seller: username='{seller.username}', password='password123', ID={seller.id}")
        
        print(f"\n💰 Wallets:")
        print(f"   • Buyer BTC:  {buyer_btc_wallet.balance} BTC")
        print(f"   • Seller BTC: {seller_btc_wallet.balance} BTC")
        
        print(f"\n🔄 P2P Trades (Ready for Dispute):")
        print(f"   • Trade #{trade.id}: {trade.amount} BTC for ${trade.total_fiat} USD")
        print(f"     Status: {trade.status}")
        print(f"     Buyer: {buyer.username} → Seller: {seller.username}")
        print(f"     ⚠️  Buyer can file dispute (claims payment sent)")
        
        if trade2:
            print(f"\n   • Trade #{trade2.id}: {trade2.amount} BTC for ${trade2.total_fiat} USD")
            print(f"     Status: {trade2.status}")
            print(f"     Buyer: {seller.username} → Seller: {buyer.username}")
            print(f"     ⚠️  Buyer can file dispute")
        
        print(f"\n🔒 Escrow:")
        print(f"   • Escrow #{escrow.id}: {escrow.amount} BTC (LOCKED)")
        if trade2:
            print(f"   • Escrow #{escrow2.id}: {escrow2.amount} BTC (LOCKED)")
        
        print("\n" + "=" * 70)
        print("🚀 READY TO TEST!")
        print("=" * 70)
        print("\n📖 Manual Testing Instructions:")
        print("\n1️⃣  START THE BACKEND:")
        print("   cd backend")
        print("   python main.py")
        
        print("\n2️⃣  START THE FRONTEND:")
        print("   cd frontend")
        print("   npm start")
        
        print("\n3️⃣  LOGIN AS BUYER:")
        print("   • Go to http://localhost:4200")
        print(f"   • Login with: username='{buyer.username}', password='password123'")
        
        print("\n4️⃣  NAVIGATE TO P2P TRADES:")
        print("   • Click 'P2P Market' in navigation")
        print("   • Click 'My Trades' tab")
        print(f"   • You should see Trade #{trade.id} with status 'PAYMENT_SENT'")
        
        print("\n5️⃣  FILE A DISPUTE:")
        print("   • Find the trade with PAYMENT_SENT status")
        print("   • Look for the '⚠️ Dispute' button (orange/gold color)")
        print("   • Click it to open the dispute modal")
        print("   • Enter a reason (e.g., 'Seller not responding after payment')")
        print("   • Click 'File Dispute'")
        
        print("\n6️⃣  VIEW YOUR DISPUTES:")
        print("   • Click 'Disputes' in the main navigation menu")
        print("   • You'll see all your disputes listed")
        print("   • Click 'View Details' to see full information")
        print("   • Add evidence if needed")
        
        print("\n7️⃣  TEST AS ADMIN (Optional):")
        print("   • Logout and login as admin")
        print("   • Go to Admin Dashboard → Disputes tab")
        print("   • See all disputes with statistics")
        print("   • Click 'View Full Details' on any dispute")
        print("   • Review trade details, parties, escrow, evidence")
        print("   • Choose 'Refund to Buyer' or 'Release to Seller'")
        print("   • Write resolution explanation")
        print("   • Click 'Resolve Dispute'")
        
        print("\n" + "=" * 70)
        print("💡 TROUBLESHOOTING:")
        print("=" * 70)
        print("\n❓ Don't see the '⚠️ Dispute' button?")
        print("   • The button only appears for trades with status:")
        print("     - PAYMENT_SENT (buyer claims to have paid)")
        print("     - DISPUTED (already in dispute)")
        print("   • Make sure you're viewing 'My Trades' tab")
        print("   • Check that the trade status is correct in database")
        
        print("\n❓ Can't find the Disputes menu?")
        print("   • Make sure you're logged in (not admin)")
        print("   • Check the navigation bar between 'P2P Market' and 'Wallet'")
        print("   • Look for a shield icon with 'Disputes' text")
        
        print("\n❓ No trades showing in My Trades?")
        print(f"   • Make sure you're logged in as '{buyer.username}' or '{seller.username}'")
        print("   • Run this script again to recreate test data")
        print("   • Check backend console for any errors")
        
        print("\n" + "=" * 70)
        print("🎉 Happy Testing!")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error setting up test data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Ensure tables exist
    print("📋 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # Setup test data
    success = setup_dispute_test_data()
    
    if success:
        print("\n✅ All done! Follow the manual testing instructions above.")
    else:
        print("\n❌ Setup failed. Check the error messages above.")
