"""
Check all tables in both databases and identify what needs to be merged
"""
import sqlite3
import os

def check_all_tables():
    """Check all tables in both databases"""
    
    root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_simulator.db")
    backend_db = os.path.join(os.path.dirname(__file__), "trading_simulator.db")
    
    print("=" * 80)
    print("Database Tables Comparison")
    print("=" * 80)
    
    source_conn = sqlite3.connect(root_db)
    target_conn = sqlite3.connect(backend_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        # Get all tables from source
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        source_tables = [row[0] for row in source_cursor.fetchall()]
        
        # Get all tables from target
        target_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        target_tables = [row[0] for row in target_cursor.fetchall()]
        
        print(f"\nRoot DB tables: {len(source_tables)}")
        print(f"Backend DB tables: {len(target_tables)}")
        
        print("\n" + "=" * 80)
        print("Row Counts Comparison")
        print("=" * 80)
        print(f"\n{'Table':<30} {'Root DB':<15} {'Backend DB':<15} {'Status'}")
        print("-" * 80)
        
        needs_merge = []
        
        for table in sorted(set(source_tables + target_tables)):
            if table.startswith('sqlite_'):
                continue
            
            # Get source count
            try:
                source_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                source_count = source_cursor.fetchone()[0]
            except:
                source_count = 0
            
            # Get target count
            try:
                target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                target_count = target_cursor.fetchone()[0]
            except:
                target_count = 0
            
            # Determine status
            if source_count == 0 and target_count == 0:
                status = "✓ Empty"
            elif source_count == target_count:
                status = "✓ Same"
            elif source_count < target_count:
                status = "✓ Target has more"
            else:
                status = "⚠️  Needs merge"
                needs_merge.append((table, source_count, target_count))
            
            print(f"{table:<30} {source_count:<15} {target_count:<15} {status}")
        
        if needs_merge:
            print("\n" + "=" * 80)
            print("Tables that need merging:")
            print("=" * 80)
            for table, src_count, tgt_count in needs_merge:
                missing = src_count - tgt_count
                print(f"  • {table}: {missing} rows need to be merged")
        else:
            print("\n" + "=" * 80)
            print("✅ All data is merged!")
            print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    check_all_tables()
