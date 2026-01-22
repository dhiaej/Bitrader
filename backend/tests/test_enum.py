from models.price_prediction import PredictionTimeframe

print("Enum values:")
print(f"  ONE_HOUR.value = {PredictionTimeframe.ONE_HOUR.value}")
print(f"  TWENTY_FOUR_HOURS.value = {PredictionTimeframe.TWENTY_FOUR_HOURS.value}")
print(f"  SEVEN_DAYS.value = {PredictionTimeframe.SEVEN_DAYS.value}")

print("\nComparison test:")
print(f"  PredictionTimeframe.ONE_HOUR == '1h' : {PredictionTimeframe.ONE_HOUR == '1h'}")
print(f"  PredictionTimeframe.ONE_HOUR.value == '1h' : {PredictionTimeframe.ONE_HOUR.value == '1h'}")

print("\nChecking DB query:")
from database import SessionLocal
from models.price_prediction import PricePrediction

db = SessionLocal()
try:
    # Query with string
    result1 = db.query(PricePrediction).filter(
        PricePrediction.symbol == "BTC",
        PricePrediction.timeframe == "1h"
    ).first()
    print(f"\nQuery with string '1h': {result1 is not None}")
    if result1:
        print(f"  Found: {result1.symbol} {result1.timeframe} confidence={result1.confidence_score}")
    
    # Query with enum
    result2 = db.query(PricePrediction).filter(
        PricePrediction.symbol == "BTC",
        PricePrediction.timeframe == PredictionTimeframe.ONE_HOUR
    ).first()
    print(f"\nQuery with enum ONE_HOUR: {result2 is not None}")
    if result2:
        print(f"  Found: {result2.symbol} {result2.timeframe} confidence={result2.confidence_score}")
finally:
    db.close()
