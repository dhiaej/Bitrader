"""
Merge price_predictions and other data from root to backend database
"""
import sqlite3
import os

def merge_price_predictions():
    """Merge price_predictions from root DB to backend DB"""
    
    root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_simulator.db")
    backend_db = os.path.join(os.path.dirname(__file__), "trading_simulator.db")
    
    print("=" * 80)
    print("Merging Price Predictions")
    print("=" * 80)
    
    source_conn = sqlite3.connect(root_db)
    target_conn = sqlite3.connect(backend_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        # Get price_predictions from source
        source_cursor.execute("SELECT COUNT(*) FROM price_predictions")
        source_count = source_cursor.fetchone()[0]
        print(f"\nSource DB: {source_count} price predictions")
        
        target_cursor.execute("SELECT COUNT(*) FROM price_predictions")
        target_count = target_cursor.fetchone()[0]
        print(f"Target DB: {target_count} price predictions")
        
        if source_count == 0:
            print("\n⚠️  No price predictions to merge")
            return
        
        # Get column names
        source_cursor.execute("PRAGMA table_info(price_predictions)")
        source_columns = [col[1] for col in source_cursor.fetchall()]
        print(f"\nColumns: {source_columns}")
        
        # Get all price predictions
        source_cursor.execute("SELECT * FROM price_predictions")
        predictions = source_cursor.fetchall()
        
        print(f"\n📊 Merging {len(predictions)} price predictions...")
        
        added = 0
        for pred in predictions:
            pred_dict = dict(zip(source_columns, pred))
            
            # Check if already exists (by symbol and created_at)
            target_cursor.execute("""
                SELECT id FROM price_predictions 
                WHERE symbol = ? AND created_at = ?
            """, (pred_dict.get('symbol'), pred_dict.get('created_at')))
            
            if target_cursor.fetchone():
                continue  # Skip duplicate
            
            # Insert into target with actual columns
            target_cursor.execute(f"""
                INSERT INTO price_predictions (
                    symbol, timeframe, predicted_direction, predicted_change,
                    confidence_score, current_price, predicted_price, reasoning,
                    recommendation, created_at, actual_price, accuracy_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pred_dict.get('symbol'),
                pred_dict.get('timeframe'),
                pred_dict.get('predicted_direction'),
                pred_dict.get('predicted_change'),
                pred_dict.get('confidence_score'),
                pred_dict.get('current_price'),
                pred_dict.get('predicted_price'),
                pred_dict.get('reasoning'),
                pred_dict.get('recommendation'),
                pred_dict.get('created_at'),
                pred_dict.get('actual_price'),
                pred_dict.get('accuracy_score')
            ))
            added += 1
        
        # Also merge price_history if it exists
        try:
            source_cursor.execute("SELECT COUNT(*) FROM price_history")
            history_count = source_cursor.fetchone()[0]
            print(f"\n📈 Found {history_count} price history records")
            
            if history_count > 0:
                source_cursor.execute("SELECT * FROM price_history")
                history_records = source_cursor.fetchall()
                
                source_cursor.execute("PRAGMA table_info(price_history)")
                history_columns = [col[1] for col in source_cursor.fetchall()]
                
                history_added = 0
                for record in history_records:
                    rec_dict = dict(zip(history_columns, record))
                    
                    # Check if already exists
                    target_cursor.execute("""
                        SELECT id FROM price_history 
                        WHERE symbol = ? AND timestamp = ?
                    """, (rec_dict.get('symbol'), rec_dict.get('timestamp')))
                    
                    if target_cursor.fetchone():
                        continue
                    
                    target_cursor.execute(f"""
                        INSERT INTO price_history (
                            symbol, timestamp, open, high, low, close, volume
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rec_dict.get('symbol'),
                        rec_dict.get('timestamp'),
                        rec_dict.get('open'),
                        rec_dict.get('high'),
                        rec_dict.get('low'),
                        rec_dict.get('close'),
                        rec_dict.get('volume')
                    ))
                    history_added += 1
                
                print(f"  ✅ Added {history_added} price history records")
        except Exception as e:
            print(f"  ⚠️  Could not merge price_history: {e}")
        
        target_conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ Merge completed!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Price predictions added: {added}")
        print(f"  • Total price predictions: {target_count + added}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        target_conn.rollback()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    merge_price_predictions()
