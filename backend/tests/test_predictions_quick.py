"""
Quick test of prediction system with demo data
"""
import asyncio
from database import SessionLocal
from services.price_prediction_service import price_prediction_service

async def test_quick():
    db = SessionLocal()
    try:
        print("\n" + "="*60)
        print("🧪 QUICK PREDICTION TEST")
        print("="*60)
        
        for symbol in ["BTC", "ETH"]:
            print(f"\n📊 Testing {symbol} prediction...")
            prediction = await price_prediction_service.generate_prediction(db, symbol, "24h")
            
            if "error" in prediction:
                print(f"❌ Error: {prediction['error']}")
            else:
                print(f"✅ Prediction Generated:")
                print(f"   Direction: {prediction['prediction'].upper()}")
                print(f"   Change: {prediction['predicted_change']:+.2f}%")
                print(f"   Confidence: {prediction['confidence']}%")
                print(f"   Recommendation: {prediction['recommendation']}")
                print(f"   Data Source: {prediction.get('data_source', 'N/A')}")
                
                if 'key_factors' in prediction:
                    print(f"   Key Factors: {len(prediction['key_factors'])} factors")
                    for factor in prediction['key_factors'][:2]:
                        print(f"      • {factor}")
        
        print("\n" + "="*60)
        print("✅ Test Complete!")
        print("="*60)
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_quick())
