#!/usr/bin/env python3
"""Quick fix for timeframe formats - runs independently"""
import sqlite3
import sys

DB_PATH = "C:/Users/ayoub/OneDrive/Bureau/pi3/backend/trading_simulator.db"

def main():
    try:
        # Connect with timeout to handle locked database
        conn = sqlite3.connect(DB_PATH, timeout=10.0)
        cursor = conn.cursor()
        
        # Show current state
        cursor.execute("SELECT timeframe, COUNT(*) FROM price_predictions GROUP BY timeframe")
        print("\n🔍 BEFORE UPDATE:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} predictions")
        
        # Update timeframes
        updates = [
            ("1h", "ONE_HOUR"),
            ("24h", "TWENTY_FOUR_HOURS"),
            ("7d", "SEVEN_DAYS")
        ]
        
        total_updated = 0
        for new_val, old_val in updates:
            cursor.execute("UPDATE price_predictions SET timeframe = ? WHERE timeframe = ?", 
                          (new_val, old_val))
            count = cursor.rowcount
            total_updated += count
            print(f"\n✅ Updated {old_val} → {new_val}: {count} rows")
        
        conn.commit()
        
        # Show final state
        cursor.execute("SELECT timeframe, COUNT(*) FROM price_predictions GROUP BY timeframe")
        print("\n✨ AFTER UPDATE:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[1]} predictions")
        
        print(f"\n🎉 SUCCESS! Updated {total_updated} total predictions")
        print("⚡ Backend will automatically reload with corrected data")
        
        cursor.close()
        conn.close()
        return 0
        
    except sqlite3.OperationalError as e:
        print(f"\n❌ Database locked: {e}")
        print("💡 The backend server is holding the database lock")
        print("📋 Please stop the backend server first, then run this script")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
