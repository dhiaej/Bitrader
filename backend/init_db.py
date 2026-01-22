"""
Database Initialization Script
Run this to create all tables in MySQL database
"""

from database import Base, engine, init_db
from models import (
    User, Wallet, Transaction, OrderBookOrder, Trade,
    P2PAdvertisement, P2PTrade, Escrow, Dispute, Reputation, Review, Notification
)

def main():
    print("🗄️  Creating database tables...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        print("\n📋 Created tables:")
        print("  - users")
        print("  - wallets")
        print("  - transactions")
        print("  - orderbook_orders")
        print("  - trades")
        print("  - p2p_advertisements")
        print("  - p2p_trades")
        print("  - escrow")
        print("  - disputes")
        print("  - reputation")
        print("  - reviews")
        print("  - notifications")
        
        print("\n🎉 Database initialization complete!")
        print("\n💡 Next steps:")
        print("  1. Start backend: python main.py")
        print("  2. Open API docs: http://localhost:8000/docs")
        print("  3. Register a user and start trading!")
        
    except Exception as e:
        print(f"\n❌ Error creating tables: {e}")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if MySQL is running")
        print("  2. Verify database 'trading_simulator' exists")
        print("  3. Check .env file for correct credentials")
        print("  4. Try: CREATE DATABASE trading_simulator;")
        return False
    
    return True

if __name__ == "__main__":
    main()
