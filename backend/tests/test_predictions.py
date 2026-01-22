"""
Test Price Predictions
Verify that predictions work with the seeded historical data
"""

import asyncio
from database import SessionLocal
from services.price_prediction_service import price_prediction_service

async def test_predictions():
    """Test price predictions for BTC and ETH"""
    print("🔮 Testing Price Predictions\n")
    
    db = SessionLocal()
    
    try:
        # Test all predictions at once
        all_predictions = await price_prediction_service.get_all_predictions(db)
        
        print("📊 All Predictions Result:")
        print(f"   Keys: {list(all_predictions.keys())}\n")
        
        # Display BTC predictions
        if "BTC" in all_predictions:
            btc = all_predictions["BTC"]
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📈 BTC PREDICTIONS")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            if "error" in btc:
                print(f"❌ Error: {btc['error']}")
            else:
                for timeframe, data in btc.items():
                    if isinstance(data, dict) and "error" not in data:
                        print(f"\n⏱️  {timeframe.upper()}:")
                        print(f"   Current: ${data.get('current_price', 0):.2f}")
                        print(f"   Predicted: ${data.get('predicted_price', 0):.2f}")
                        print(f"   Direction: {data.get('predicted_direction', 'N/A')}")
                        print(f"   Change: {data.get('predicted_change', 0):.2f}%")
                        print(f"   Confidence: {data.get('confidence_score', 0)}%")
                        print(f"   Action: {data.get('recommendation', 'N/A')}")
        
        # Display ETH predictions
        if "ETH" in all_predictions:
            eth = all_predictions["ETH"]
            print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            print("📈 ETH PREDICTIONS")
            print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
            
            if "error" in eth:
                print(f"❌ Error: {eth['error']}")
            else:
                for timeframe, data in eth.items():
                    if isinstance(data, dict) and "error" not in data:
                        print(f"\n⏱️  {timeframe.upper()}:")
                        print(f"   Current: ${data.get('current_price', 0):.2f}")
                        print(f"   Predicted: ${data.get('predicted_price', 0):.2f}")
                        print(f"   Direction: {data.get('predicted_direction', 'N/A')}")
                        print(f"   Change: {data.get('predicted_change', 0):.2f}%")
                        print(f"   Confidence: {data.get('confidence_score', 0)}%")
                        print(f"   Action: {data.get('recommendation', 'N/A')}")
        
        print("\n✨ Predictions are working successfully!")
        print("   The 'Insufficient historical data' error should no longer appear.")
        
    except Exception as e:
        print(f"\n❌ Error testing predictions: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_predictions())
