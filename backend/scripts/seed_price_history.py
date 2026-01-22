"""
Seed Price History Database
Populate with historical price data for immediate predictions
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models.price_prediction import PriceHistory
from services.market_data_service import market_data_service
from datetime import datetime, timedelta, timezone
import random

def seed_price_history():
    """
    Seed historical price data for BTC and ETH
    Creates data points for the last 7 days (hourly)
    """
    print("🕒 Seeding historical price data...")
    
    db = SessionLocal()
    
    try:
        # Ensure tables exist
        Base.metadata.create_all(bind=engine)
        
        # Get current prices (or use defaults if service not started)
        current_prices = {
            "BTC": 45000.0,  # Default fallback
            "ETH": 3000.0,
            "USDT": 1.0
        }
        
        # Try to get real current prices
        try:
            market_data_service.start()
            import time
            time.sleep(2)  # Wait for initial fetch
            btc_price = market_data_service.get_price("BTC-USD")
            eth_price = market_data_service.get_price("ETH-USD")
            if btc_price:
                current_prices["BTC"] = btc_price
            if eth_price:
                current_prices["ETH"] = eth_price
            market_data_service.stop()
        except:
            print("  ⚠️  Using default prices (market data service not available)")
        
        # Generate 7 days of hourly historical data (168 hours)
        hours_to_seed = 168
        
        for symbol in ["BTC", "ETH"]:
            print(f"\n  📈 Generating {hours_to_seed} hours of data for {symbol}...")
            
            base_price = current_prices[symbol]
            
            for hour in range(hours_to_seed, 0, -1):
                # Calculate timestamp
                timestamp = datetime.now(timezone.utc) - timedelta(hours=hour)
                
                # Simulate realistic price movement (random walk)
                # More recent = closer to current price
                volatility = 0.02 if symbol == "BTC" else 0.03  # 2-3% volatility
                random_change = random.uniform(-volatility, volatility)
                price = base_price * (1 + random_change * (hour / hours_to_seed))
                
                # Calculate change percent
                if hour < hours_to_seed:
                    prev_price = base_price * (1 + random.uniform(-volatility, volatility) * ((hour + 1) / hours_to_seed))
                    change_percent = ((price - prev_price) / prev_price) * 100
                else:
                    change_percent = 0.0
                
                # Create price history record
                price_history = PriceHistory(
                    symbol=symbol,
                    price=price,
                    change_percent=change_percent,
                    volume=random.uniform(1000000, 10000000),  # Simulated volume
                    market_cap=price * random.uniform(500000000, 1000000000),  # Simulated market cap
                    source="seeded_data",
                    timestamp=timestamp
                )
                
                db.add(price_history)
                
                # Commit in batches
                if (hours_to_seed - hour + 1) % 24 == 0:
                    db.commit()
                    print(f"    ✓ Added {hours_to_seed - hour + 1}/{hours_to_seed} records")
            
            db.commit()
            print(f"  ✅ Completed {symbol} - {hours_to_seed} data points created")
        
        # Verify data
        btc_count = db.query(PriceHistory).filter(PriceHistory.symbol == "BTC").count()
        eth_count = db.query(PriceHistory).filter(PriceHistory.symbol == "ETH").count()
        
        print(f"\n📊 Database Summary:")
        print(f"  BTC price history records: {btc_count}")
        print(f"  ETH price history records: {eth_count}")
        print(f"\n🎉 Price history seeding complete!")
        print(f"   Price predictions will now work with {hours_to_seed} hours of historical data!")
        
    except Exception as e:
        print(f"\n❌ Error seeding price history: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    seed_price_history()
