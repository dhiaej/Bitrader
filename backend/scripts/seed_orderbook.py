"""
Seed the order book with test data
Run: python seed_orderbook.py
"""

import sqlite3
from datetime import datetime
from decimal import Decimal
import random

def seed_orderbook():
    conn = sqlite3.connect('trading_simulator.db')
    cursor = conn.cursor()
    
    # Trading pairs for all supported cryptocurrencies
    instruments = [
        'BTC/USD', 'BTC/USDT', 'ETH/USD', 'ETH/USDT',
        'BNB/USD', 'BNB/USDT', 'XRP/USD', 'XRP/USDT',
        'ADA/USD', 'ADA/USDT', 'SOL/USD', 'SOL/USDT',
        'DOGE/USD', 'DOGE/USDT', 'DOT/USD', 'DOT/USDT',
        'MATIC/USD', 'MATIC/USDT', 'AVAX/USD', 'AVAX/USDT',
        'LINK/USD', 'LINK/USDT', 'UNI/USD', 'UNI/USDT',
        'ATOM/USD', 'ATOM/USDT', 'LTC/USD', 'LTC/USDT',
        'SHIB/USD', 'SHIB/USDT', 'TRX/USD', 'TRX/USDT',
        'ARB/USD', 'ARB/USDT', 'OP/USD', 'OP/USDT'
    ]
    
    # Base prices for each instrument (approximate market prices)
    base_prices = {
        'BTC/USD': 43000, 'BTC/USDT': 43050,
        'ETH/USD': 2300, 'ETH/USDT': 2305,
        'BNB/USD': 310, 'BNB/USDT': 311,
        'XRP/USD': 0.62, 'XRP/USDT': 0.621,
        'ADA/USD': 0.58, 'ADA/USDT': 0.581,
        'SOL/USD': 95, 'SOL/USDT': 95.5,
        'DOGE/USD': 0.095, 'DOGE/USDT': 0.096,
        'DOT/USD': 7.2, 'DOT/USDT': 7.21,
        'MATIC/USD': 0.88, 'MATIC/USDT': 0.881,
        'AVAX/USD': 38, 'AVAX/USDT': 38.1,
        'LINK/USD': 15, 'LINK/USDT': 15.05,
        'UNI/USD': 6.5, 'UNI/USDT': 6.51,
        'ATOM/USD': 10.2, 'ATOM/USDT': 10.21,
        'LTC/USD': 72, 'LTC/USDT': 72.1,
        'SHIB/USD': 0.000010, 'SHIB/USDT': 0.0000101,
        'TRX/USD': 0.105, 'TRX/USDT': 0.1051,
        'ARB/USD': 1.25, 'ARB/USDT': 1.251,
        'OP/USD': 2.35, 'OP/USDT': 2.351
    }
    
    print("🚀 Seeding orderbook with test data...")
    
    # Get admin user (id=1) or create one
    cursor.execute("SELECT id FROM users WHERE id = 1")
    if not cursor.fetchone():
        print("⚠️  No user found. Creating admin user first...")
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role)
            VALUES ('admin', 'admin@trade.com', 'hashed_password', 'ADMIN')
        """)
        conn.commit()
    
    # Get users for orders
    cursor.execute("SELECT id FROM users LIMIT 5")
    users = [row[0] for row in cursor.fetchall()]
    
    if not users:
        print("❌ No users found. Please seed users first.")
        return
    
    print(f"✅ Found {len(users)} users")
    
    # Clear existing orders
    cursor.execute("DELETE FROM orderbook_orders")
    cursor.execute("DELETE FROM trades")
    conn.commit()
    print("🗑️  Cleared existing orders and trades")
    
    orders_created = 0
    
    for instrument in instruments:
        base_price = base_prices[instrument]
        
        # Create buy orders (bids) - below market price
        for i in range(15):
            user_id = random.choice(users)
            price = base_price * (0.95 - (i * 0.01))  # 95% down to 81% of base
            quantity = random.uniform(0.01, 0.5)
            
            cursor.execute("""
                INSERT INTO orderbook_orders 
                (user_id, instrument, order_type, order_subtype, price, quantity, remaining_quantity, status, created_at)
                VALUES (?, ?, 'BUY', 'LIMIT', ?, ?, ?, 'PENDING', ?)
            """, (user_id, instrument, price, quantity, quantity, datetime.utcnow()))
            orders_created += 1
        
        # Create sell orders (asks) - above market price
        for i in range(15):
            user_id = random.choice(users)
            price = base_price * (1.05 + (i * 0.01))  # 105% up to 119% of base
            quantity = random.uniform(0.01, 0.5)
            
            cursor.execute("""
                INSERT INTO orderbook_orders 
                (user_id, instrument, order_type, order_subtype, price, quantity, remaining_quantity, status, created_at)
                VALUES (?, ?, 'SELL', 'LIMIT', ?, ?, ?, 'PENDING', ?)
            """, (user_id, instrument, price, quantity, quantity, datetime.utcnow()))
            orders_created += 1
        
        # Create a few recent trades for last_price
        for i in range(3):
            trade_price = base_price * random.uniform(0.99, 1.01)
            trade_qty = random.uniform(0.01, 0.1)
            trade_amount = trade_price * trade_qty
            
            cursor.execute("""
                INSERT INTO trades 
                (order_id, buyer_id, seller_id, instrument, price, quantity, total_amount, fee, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # dummy order_id
                random.choice(users),
                random.choice(users),
                instrument,
                trade_price,
                trade_qty,
                trade_amount,
                trade_amount * 0.001,
                datetime.utcnow()
            ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Created {orders_created} orders across {len(instruments)} instruments")
    print(f"✅ Created {len(instruments) * 3} trades for price history")
    print("\n📊 Orderbook Summary:")
    
    # Show summary
    conn = sqlite3.connect('trading_simulator.db')
    cursor = conn.cursor()
    
    for instrument in instruments:
        cursor.execute("""
            SELECT order_type, COUNT(*), AVG(price), SUM(quantity)
            FROM orderbook_orders
            WHERE instrument = ? AND status = 'PENDING'
            GROUP BY order_type
        """, (instrument,))
        
        print(f"\n  {instrument}:")
        for row in cursor.fetchall():
            order_type, count, avg_price, total_qty = row
            print(f"    {order_type}: {count} orders, avg price ${avg_price:.2f}, total {total_qty:.4f}")
    
    conn.close()
    print("\n🎉 Orderbook seeding complete! Start backend and check frontend.")

if __name__ == "__main__":
    seed_orderbook()
