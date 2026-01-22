"""
Merge data from root trading_simulator.db into backend trading_simulator.db
"""
import sqlite3
import os
from datetime import datetime

def merge_databases():
    """Merge users and related data from root DB to backend DB"""
    
    root_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_simulator.db")
    backend_db = os.path.join(os.path.dirname(__file__), "trading_simulator.db")
    
    print("=" * 80)
    print("Database Merge Script")
    print("=" * 80)
    print(f"\nSource (Root): {root_db}")
    print(f"Target (Backend): {backend_db}")
    
    if not os.path.exists(root_db):
        print(f"\n❌ Error: Source database not found at {root_db}")
        return
    
    if not os.path.exists(backend_db):
        print(f"\n❌ Error: Target database not found at {backend_db}")
        return
    
    # Connect to both databases
    source_conn = sqlite3.connect(root_db)
    target_conn = sqlite3.connect(backend_db)
    
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()
    
    try:
        print("\n📊 Analyzing databases...")
        
        # Get source users
        source_cursor.execute("SELECT * FROM users")
        source_users = source_cursor.fetchall()
        source_cursor.execute("PRAGMA table_info(users)")
        source_columns = [col[1] for col in source_cursor.fetchall()]
        
        print(f"\nSource DB: {len(source_users)} users")
        print(f"Source columns: {source_columns}")
        
        # Get target users
        target_cursor.execute("SELECT username FROM users")
        existing_usernames = set(row[0] for row in target_cursor.fetchall())
        
        print(f"Target DB: {len(existing_usernames)} existing users")
        print(f"Existing usernames: {existing_usernames}")
        
        # Get target columns
        target_cursor.execute("PRAGMA table_info(users)")
        target_columns = [col[1] for col in target_cursor.fetchall()]
        print(f"Target columns: {target_columns}")
        
        # Merge users
        users_added = 0
        users_skipped = 0
        
        print("\n👥 Merging users...")
        
        for user_data in source_users:
            user_dict = dict(zip(source_columns, user_data))
            username = user_dict.get('username')
            
            # Skip if user already exists
            if username in existing_usernames:
                print(f"  ⏭️  Skipping {username} (already exists)")
                users_skipped += 1
                continue
            
            # Map source columns to target columns
            target_cursor.execute(f"""
                INSERT INTO users (
                    username, email, hashed_password, full_name, avatar_url,
                    face_embedding, is_active, is_verified, is_admin,
                    created_at, updated_at, last_login
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_dict.get('username'),
                user_dict.get('email'),
                user_dict.get('hashed_password'),
                user_dict.get('full_name'),
                None,  # avatar_url (may not exist in source)
                None,  # face_embedding (may not exist in source)
                user_dict.get('is_active', 1),
                user_dict.get('is_verified', 0),
                user_dict.get('is_admin', 0),
                user_dict.get('created_at', datetime.now().isoformat()),
                user_dict.get('updated_at'),
                user_dict.get('last_login')
            ))
            
            user_id = target_cursor.lastrowid
            print(f"  ✅ Added user: {username} (ID: {user_id})")
            users_added += 1
            
            # Add wallets for the new user
            source_cursor.execute("SELECT * FROM wallets WHERE user_id = ?", (user_dict['id'],))
            wallets = source_cursor.fetchall()
            
            if wallets:
                source_cursor.execute("PRAGMA table_info(wallets)")
                wallet_columns = [col[1] for col in source_cursor.fetchall()]
                
                for wallet_data in wallets:
                    wallet_dict = dict(zip(wallet_columns, wallet_data))
                    target_cursor.execute(f"""
                        INSERT INTO wallets (
                            user_id, currency, available_balance, locked_balance,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user_id,  # Use new user_id
                        wallet_dict.get('currency'),
                        wallet_dict.get('available_balance', 0),
                        wallet_dict.get('locked_balance', 0),
                        wallet_dict.get('created_at', datetime.now().isoformat()),
                        wallet_dict.get('updated_at')
                    ))
                    print(f"    💰 Added wallet: {wallet_dict.get('currency')}")
            
            # Add reputation for the new user
            source_cursor.execute("SELECT * FROM reputation WHERE user_id = ?", (user_dict['id'],))
            reputation = source_cursor.fetchone()
            
            if reputation:
                source_cursor.execute("PRAGMA table_info(reputation)")
                rep_columns = [col[1] for col in source_cursor.fetchall()]
                rep_dict = dict(zip(rep_columns, reputation))
                
                target_cursor.execute(f"""
                    INSERT INTO reputation (
                        user_id, score, total_trades, completed_trades, disputed_trades,
                        completion_rate, average_response_time, average_rating,
                        review_count, badges, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,  # Use new user_id
                    rep_dict.get('score', 100),
                    rep_dict.get('total_trades', 0),
                    rep_dict.get('completed_trades', 0),
                    rep_dict.get('disputed_trades', 0),
                    rep_dict.get('completion_rate', 0.0),
                    rep_dict.get('average_response_time', 0.0),
                    rep_dict.get('average_rating', 0.0),
                    rep_dict.get('review_count', 0),
                    rep_dict.get('badges'),
                    rep_dict.get('created_at', datetime.now().isoformat()),
                    rep_dict.get('updated_at')
                ))
                print(f"    ⭐ Added reputation")
        
        # Commit changes
        target_conn.commit()
        
        print("\n" + "=" * 80)
        print("✅ Merge completed successfully!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Users added: {users_added}")
        print(f"  • Users skipped: {users_skipped}")
        print(f"  • Total users now: {len(existing_usernames) + users_added}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        target_conn.rollback()
        print(f"\n❌ Error during merge: {e}")
        import traceback
        traceback.print_exc()
    finally:
        source_conn.close()
        target_conn.close()


if __name__ == "__main__":
    merge_databases()
