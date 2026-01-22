"""Regenerate all predictions with correct prices"""
import sys
sys.path.insert(0, '.')
from database import SessionLocal
from services.price_prediction_service import price_prediction_service
from models.price_prediction import PricePrediction
import asyncio
import time

# Wait for services to initialize
print("⏳ Waiting for market data service to fetch prices...")
time.sleep(3)

db = SessionLocal()
try:
    # Clear old predictions
    print("\n🗑️  Clearing old predictions...")
    db.query(PricePrediction).delete()
    db.commit()
    print("✅ Old predictions cleared")
    
    # Generate new predictions for each cryptocurrency
    symbols = ["BTC", "ETH", "LTC", "SOL", "DOGE"]
    timeframe = "24h"
    
    print(f"\n🔮 Generating predictions for {len(symbols)} cryptocurrencies...")
    for symbol in symbols:
        try:
            print(f"\n  Processing {symbol}...")
            prediction = asyncio.run(
                price_prediction_service.generate_prediction(db, symbol, timeframe)
            )
            
            if prediction:
                print(f"  ✅ {symbol}: {prediction['prediction'].upper()} "
                      f"{prediction['predicted_change']:+.2f}% "
                      f"(confidence: {prediction['confidence']}%)")
                print(f"     Current: ${prediction['current_price']:,.2f} → "
                      f"Target: ${prediction['predicted_price']:,.2f}")
            else:
                print(f"  ❌ Failed to generate prediction for {symbol}")
                
        except Exception as e:
            print(f"  ❌ Error generating prediction for {symbol}: {e}")
    
    print("\n✅ Prediction generation complete!")
    
    # Show summary
    print("\n📊 Database Summary:")
    predictions = db.query(PricePrediction).all()
    print(f"   Total predictions stored: {len(predictions)}")
    for pred in predictions:
        print(f"   - {pred.symbol}: ${pred.current_price:,.2f} → ${pred.predicted_price:,.2f} "
              f"({pred.predicted_change:+.2f}%)")
    
finally:
    db.close()
