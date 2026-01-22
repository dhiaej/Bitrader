"""
Merge remaining p2p_advertisements from root to backend
"""
import sqlite3
import os

def merge_p2p_ads():
    """Merge p2p_advertisements from root DB to backend DB"""
    
    root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_simulator.db")
    backend_db = os.path.join(os.path.dirname(__file__), "trading_simulator.db")
    
    print("=" * 80)
    print("Merging P2P Advertisements")
    print("=" * 80)
    
    source_conn = sqlite3.connect(root_db)
    target_conn = sqlite3.connect(backend_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        # Get all p2p_advertisements from source
        source_cursor.execute("SELECT * FROM p2p_advertisements")
        source_ads = source_cursor.fetchall()
        
        source_cursor.execute("PRAGMA table_info(p2p_advertisements)")
        source_columns = [col[1] for col in source_cursor.fetchall()]
        
        print(f"\nSource DB: {len(source_ads)} p2p_advertisements")
        print(f"Columns: {source_columns}")
        
        # Get target count
        target_cursor.execute("SELECT COUNT(*) FROM p2p_advertisements")
        target_count = target_cursor.fetchone()[0]
        print(f"Target DB: {target_count} p2p_advertisements")
        
        # Create a map of old user_id to new user_id
        print("\n📊 Creating user ID mapping...")
        user_map = {}
        
        source_cursor.execute("SELECT id, username FROM users")
        source_users = source_cursor.fetchall()
        
        for old_id, username in source_users:
            target_cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = target_cursor.fetchone()
            if result:
                user_map[old_id] = result[0]
                print(f"  User '{username}': {old_id} -> {user_map[old_id]}")
        
        print(f"\n📢 Merging p2p_advertisements...")
        added = 0
        skipped = 0
        
        for ad_data in source_ads:
            ad_dict = dict(zip(source_columns, ad_data))
            old_user_id = ad_dict.get('user_id')
            
            # Skip if user doesn't exist in target
            if old_user_id not in user_map:
                print(f"  ⏭️  Skipping ad {ad_dict.get('id')} - user {old_user_id} not found")
                skipped += 1
                continue
            
            new_user_id = user_map[old_user_id]
            
            # Check if similar ad already exists (same user, currency, ad_type)
            target_cursor.execute("""
                SELECT id FROM p2p_advertisements 
                WHERE user_id = ? AND currency = ? AND ad_type = ? AND price = ?
            """, (new_user_id, ad_dict.get('currency'), ad_dict.get('ad_type'), ad_dict.get('price')))
            
            if target_cursor.fetchone():
                skipped += 1
                continue  # Skip duplicate
            
            # Insert with new user_id
            target_cursor.execute(f"""
                INSERT INTO p2p_advertisements (
                    user_id, ad_type, currency, fiat_currency, price,
                    min_limit, max_limit, available_amount, payment_methods,
                    payment_time_limit, terms_conditions, is_active,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_user_id,
                ad_dict.get('ad_type'),
                ad_dict.get('currency'),
                ad_dict.get('fiat_currency'),
                ad_dict.get('price'),
                ad_dict.get('min_limit'),
                ad_dict.get('max_limit'),
                ad_dict.get('available_amount'),
                ad_dict.get('payment_methods'),
                ad_dict.get('payment_time_limit'),
                ad_dict.get('terms_conditions'),
                ad_dict.get('is_active', 1),
                ad_dict.get('created_at'),
                ad_dict.get('updated_at')
            ))
            added += 1
            print(f"  ✅ Added {ad_dict.get('ad_type')} ad for {ad_dict.get('currency')} by user {new_user_id}")
        
        target_conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ Merge completed!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • P2P ads added: {added}")
        print(f"  • P2P ads skipped: {skipped}")
        print(f"  • Total P2P ads now: {target_count + added}")
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
    merge_p2p_ads()
