"""
Seed Database with Sample Data
Creates test users and initial data for development/testing
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, Wallet, Reputation, P2PAdvertisement, OrderType
from utils.auth import get_password_hash
from decimal import Decimal
from config import settings
import json

def seed_database():
    """Populate database with sample data"""
    
    print("🌱 Seeding database with sample data...")
    
    db = SessionLocal()
    
    try:
        # Create test users
        test_users = [
            {
                "username": "alice_trader",
                "email": "alice@example.com",
                "password": "password123",
                "full_name": "Alice Johnson"
            },
            {
                "username": "bob_crypto",
                "email": "bob@example.com",
                "password": "password123",
                "full_name": "Bob Smith"
            },
            {
                "username": "charlie_btc",
                "email": "charlie@example.com",
                "password": "password123",
                "full_name": "Charlie Davis"
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.username == user_data["username"]).first()
            if existing_user:
                print(f"  ⏭️  User {user_data['username']} already exists, skipping...")
                created_users.append(existing_user)
                continue
            
            # Create user
            user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                is_active=True,
                is_verified=True
            )
            db.add(user)
            db.flush()
            
            # Create wallets with initial balances
            wallets_config = [
                ("USD", settings.INITIAL_USD_BALANCE),
                ("BTC", settings.INITIAL_BTC_BALANCE),
                ("ETH", settings.INITIAL_ETH_BALANCE),
                ("USDT", settings.INITIAL_USDT_BALANCE),
            ]
            
            for currency, initial_balance in wallets_config:
                wallet = Wallet(
                    user_id=user.id,
                    currency=currency,
                    available_balance=Decimal(str(initial_balance)),
                    locked_balance=Decimal("0.0")
                )
                db.add(wallet)
            
            # Create reputation
            reputation = Reputation(
                user_id=user.id,
                score=settings.INITIAL_REPUTATION_SCORE,
                total_trades=0,
                completed_trades=0,
                completion_rate=0.0
            )
            db.add(reputation)
            
            created_users.append(user)
            print(f"  ✅ Created user: {user_data['username']}")
        
        db.commit()
        
        # Create sample P2P advertisements
        sample_ads = [
            {
                "user_id": created_users[0].id,
                "ad_type": OrderType.SELL,
                "currency": "BTC",
                "fiat_currency": "USD",
                "price": Decimal("45000.00"),
                "min_limit": Decimal("100.00"),
                "max_limit": Decimal("5000.00"),
                "available_amount": Decimal("0.2"),
                "payment_methods": json.dumps(["Bank Transfer", "PayPal"]),
                "payment_time_limit": 30,
                "terms_conditions": "Fast and reliable BTC seller. Online 24/7."
            },
            {
                "user_id": created_users[1].id,
                "ad_type": OrderType.BUY,
                "currency": "ETH",
                "fiat_currency": "USD",
                "price": Decimal("3000.00"),
                "min_limit": Decimal("50.00"),
                "max_limit": Decimal("2000.00"),
                "available_amount": Decimal("2.0"),
                "payment_methods": json.dumps(["Bank Transfer", "Wise"]),
                "payment_time_limit": 20,
                "terms_conditions": "Looking to buy ETH. Quick payment."
            },
            {
                "user_id": created_users[2].id,
                "ad_type": OrderType.SELL,
                "currency": "USDT",
                "fiat_currency": "USD",
                "price": Decimal("1.00"),
                "min_limit": Decimal("20.00"),
                "max_limit": Decimal("1000.00"),
                "available_amount": Decimal("3000.00"),
                "payment_methods": json.dumps(["Bank Transfer", "PayPal", "Venmo"]),
                "payment_time_limit": 15,
                "terms_conditions": "Selling USDT at 1:1. Fast transfers!"
            }
        ]
        
        for ad_data in sample_ads:
            ad = P2PAdvertisement(**ad_data)
            db.add(ad)
        
        db.commit()
        print("\n  ✅ Created sample P2P advertisements")
        
        print("\n🎉 Database seeding complete!")
        print("\n📋 Test Accounts Created:")
        print("  Username: alice_trader | Password: password123")
        print("  Username: bob_crypto   | Password: password123")
        print("  Username: charlie_btc  | Password: password123")
        print("\n💰 Each account has:")
        print(f"  - ${settings.INITIAL_USD_BALANCE:,.2f} USD")
        print(f"  - {settings.INITIAL_BTC_BALANCE} BTC")
        print(f"  - {settings.INITIAL_ETH_BALANCE} ETH")
        print(f"  - ${settings.INITIAL_USDT_BALANCE:,.2f} USDT")
        print("\n🚀 Start the server and login with any test account!")
        
    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    # Ensure tables exist first
    print("📋 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # Seed data
    seed_database()
