"""
Test if BTC and ETH predictions are different
"""
import asyncio
from database import SessionLocal
from services.price_prediction_service import price_prediction_service

async def test_different_predictions():
    db = SessionLocal()
    try:
        print("\n🧪 Testing if predictions differ between cryptocurrencies...\n")
        
        btc = await price_prediction_service.generate_prediction(db, 'BTC', '24h')
        eth = await price_prediction_service.generate_prediction(db, 'ETH', '24h')
        
        print(f"BTC Prediction:")
        print(f"  Direction: {btc['prediction']}")
        print(f"  Change: {btc['predicted_change']}%")
        print(f"  Confidence: {btc['confidence']}%")
        print(f"  Current Price: ${btc['current_price']:,.2f}")
        print(f"  Predicted Price: ${btc['predicted_price']:,.2f}")
        
        print(f"\nETH Prediction:")
        print(f"  Direction: {eth['prediction']}")
        print(f"  Change: {eth['predicted_change']}%")
        print(f"  Confidence: {eth['confidence']}%")
        print(f"  Current Price: ${eth['current_price']:,.2f}")
        print(f"  Predicted Price: ${eth['predicted_price']:,.2f}")
        
        # Check if they're the same
        if (btc['predicted_change'] == eth['predicted_change'] and 
            btc['confidence'] == eth['confidence']):
            print("\n❌ PROBLEM: BTC and ETH have identical predictions!")
            print("   This shouldn't happen - each crypto should have unique analysis.")
        else:
            print("\n✅ GOOD: BTC and ETH have different predictions!")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_different_predictions())
