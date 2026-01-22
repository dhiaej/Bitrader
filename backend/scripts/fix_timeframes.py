"""
Fix timeframe format in price_predictions table
"""
import sqlite3
import os

def fix_timeframe_formats():
    """Convert old timeframe format to new enum format"""
    
    backend_db = os.path.join(os.path.dirname(__file__), "trading_simulator.db")
    
    print("=" * 80)
    print("Fixing Price Prediction Timeframe Formats")
    print("=" * 80)
    
    conn = sqlite3.connect(backend_db)
    cursor = conn.cursor()
    
    try:
        # Check current formats
        cursor.execute("SELECT DISTINCT timeframe FROM price_predictions")
        current_formats = [row[0] for row in cursor.fetchall()]
        print(f"\nCurrent timeframe formats: {current_formats}")
        
        # Mapping of old to new formats
        format_map = {
            "ONE_HOUR": "1h",
            "TWENTY_FOUR_HOURS": "24h",
            "SEVEN_DAYS": "7d"
        }
        
        updated = 0
        for old_format, new_format in format_map.items():
            cursor.execute(
                "UPDATE price_predictions SET timeframe = ? WHERE timeframe = ?",
                (new_format, old_format)
            )
            count = cursor.rowcount
            if count > 0:
                print(f"  ✅ Updated {count} predictions: {old_format} -> {new_format}")
                updated += count
        
        conn.commit()
        
        # Verify
        cursor.execute("SELECT DISTINCT timeframe FROM price_predictions")
        new_formats = [row[0] for row in cursor.fetchall()]
        print(f"\nNew timeframe formats: {new_formats}")
        
        cursor.execute("SELECT COUNT(*) FROM price_predictions")
        total = cursor.fetchone()[0]
        
        print("\n" + "=" * 80)
        print("✅ Timeframe formats fixed!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Predictions updated: {updated}")
        print(f"  • Total predictions: {total}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == "__main__":
    fix_timeframe_formats()
