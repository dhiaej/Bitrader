"""
Quick Database Seeding - No User Input Required
Creates test users for login
"""

import sys
import os
from datetime import datetime
from decimal import Decimal
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faker import Faker
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Wallet, Reputation
from utils.auth import get_password_hash

fake = Faker()
Faker.seed(42)
random.seed(42)


def create_test_users(db: Session):
    """Create test users for login"""
    print("\n👥 Creating test users...")
    
    # Create admin user
    admin = User(
        username="admin",
        email="admin@test.com",
        hashed_password=get_password_hash("admin123"),
        full_name="Admin User",
        avatar_url="https://i.pravatar.cc/150?u=admin",
        is_active=True,
        is_verified=True,
        is_admin=True,
        created_at=datetime.now()
    )
    db.add(admin)
    db.flush()
    
    # Create wallets for admin
    for currency in ["USD", "BTC", "ETH", "USDT"]:
        if currency == "USD":
            available = Decimal("50000.00")
        elif currency == "BTC":
            available = Decimal("1.5")
        elif currency == "ETH":
            available = Decimal("10.0")
        else:
            available = Decimal("25000.00")
        
        wallet = Wallet(
            user_id=admin.id,
            currency=currency,
            available_balance=available,
            locked_balance=Decimal("0")
        )
        db.add(wallet)
    
    # Create reputation for admin
    reputation = Reputation(
        user_id=admin.id,
        score=1000,
        total_trades=50,
        completed_trades=48,
        completion_rate=96.0
    )
    db.add(reputation)
    
    print(f"  ✅ Created admin user: admin / admin123")
    
    # Create test user
    testuser = User(
        username="testuser",
        email="test@test.com",
        hashed_password=get_password_hash("password123"),
        full_name="Test User",
        avatar_url="https://i.pravatar.cc/150?u=testuser",
        is_active=True,
        is_verified=True,
        is_admin=False,
        created_at=datetime.now()
    )
    db.add(testuser)
    db.flush()
    
    # Create wallets for test user
    for currency in ["USD", "BTC", "ETH", "USDT"]:
        if currency == "USD":
            available = Decimal("10000.00")
        elif currency == "BTC":
            available = Decimal("0.5")
        elif currency == "ETH":
            available = Decimal("5.0")
        else:
            available = Decimal("5000.00")
        
        wallet = Wallet(
            user_id=testuser.id,
            currency=currency,
            available_balance=available,
            locked_balance=Decimal("0")
        )
        db.add(wallet)
    
    # Create reputation for test user
    reputation = Reputation(
        user_id=testuser.id,
        score=100,
        total_trades=0,
        completed_trades=0,
        completion_rate=0.0
    )
    db.add(reputation)
    
    print(f"  ✅ Created test user: testuser / password123")
    
    # Create a few more random users
    for i in range(5):
        username = f"user{i+1}"
        user = User(
            username=username,
            email=f"user{i+1}@test.com",
            hashed_password=get_password_hash("password123"),
            full_name=fake.name(),
            avatar_url=f"https://i.pravatar.cc/150?u={username}",
            is_active=True,
            is_verified=True,
            is_admin=False,
            created_at=datetime.now()
        )
        db.add(user)
        db.flush()
        
        # Create wallets
        for currency in ["USD", "BTC", "ETH", "USDT"]:
            if currency == "USD":
                available = Decimal(str(random.uniform(5000, 20000)))
            elif currency == "BTC":
                available = Decimal(str(random.uniform(0.1, 1.0)))
            elif currency == "ETH":
                available = Decimal(str(random.uniform(1.0, 8.0)))
            else:
                available = Decimal(str(random.uniform(2000, 10000)))
            
            wallet = Wallet(
                user_id=user.id,
                currency=currency,
                available_balance=available,
                locked_balance=Decimal("0")
            )
            db.add(wallet)
        
        # Create reputation
        reputation = Reputation(
            user_id=user.id,
            score=random.randint(50, 500),
            total_trades=random.randint(0, 20),
            completed_trades=random.randint(0, 15),
            completion_rate=random.uniform(80, 100)
        )
        db.add(reputation)
        
        print(f"  ✅ Created user: {username} / password123")
    
    db.commit()
    print(f"\n✅ Created 7 test users successfully!")


def main():
    print("=" * 80)
    print("🌱 Quick Database Seeding")
    print("=" * 80)
    
    db = SessionLocal()
    
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        if existing_users > 0:
            print(f"\n⚠️  Database already has {existing_users} users.")
            print("   Skipping seed to avoid duplicates.")
            print("\n💡 If you want to reseed, delete the database file and run init_db.py first.")
            return
        
        create_test_users(db)
        
        print("\n" + "=" * 80)
        print("✅ Seeding completed successfully!")
        print("=" * 80)
        print(f"\n🔑 Login Credentials:")
        print(f"   Admin: admin / admin123")
        print(f"   User:  testuser / password123")
        print(f"   Other: user1 through user5 / password123")
        print("\n" + "=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
