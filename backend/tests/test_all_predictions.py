"""
Test predictions for all 5 cryptocurrencies
"""
import asyncio
from database import SessionLocal
from services.price_prediction_service import price_prediction_service

async def test_all_cryptos():
    db = SessionLocal()
    try:
        print("\n" + "="*70)
        print("🧪 TESTING ALL CRYPTOCURRENCY PREDICTIONS")
        print("="*70 + "\n")
        
        symbols = ["BTC", "ETH", "LTC", "SOL", "DOGE"]
        predictions = {}
        
        for symbol in symbols:
            print(f"📊 Generating {symbol} prediction...")
            pred = await price_prediction_service.generate_prediction(db, symbol, "24h")
            predictions[symbol] = pred
            
        print("\n" + "="*70)
        print("📈 PREDICTION SUMMARY")
        print("="*70 + "\n")
        
        for symbol, pred in predictions.items():
            direction_emoji = "🟢" if pred['prediction'] == 'up' else "🔴" if pred['prediction'] == 'down' else "⚪"
            print(f"{direction_emoji} {symbol:5s} | {pred['predicted_change']:+6.2f}% | {pred['confidence']:3d}% conf | {pred['recommendation']:4s} | ${pred['current_price']:>10,.2f}")
        
        print("\n" + "="*70)
        
        # Check for uniqueness
        changes = [p['predicted_change'] for p in predictions.values()]
        confidences = [p['confidence'] for p in predictions.values()]
        
        unique_changes = len(set(changes))
        unique_confidences = len(set(confidences))
        
        print(f"\n📊 Diversity Check:")
        print(f"   Unique prediction changes: {unique_changes}/5")
        print(f"   Unique confidence levels: {unique_confidences}/5")
        
        if unique_changes >= 4 and unique_confidences >= 3:
            print("\n✅ EXCELLENT: Predictions show good diversity!")
        elif unique_changes >= 3:
            print("\n✅ GOOD: Predictions are reasonably diverse")
        else:
            print("\n⚠️  WARNING: Predictions might be too similar")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_all_cryptos())
