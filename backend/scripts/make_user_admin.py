"""
Make User Admin Script
Grant admin privileges to a user by username
"""
import sys
import sqlite3
from pathlib import Path

def make_user_admin(username: str):
    """Grant admin privileges to a user"""
    
    # Get the database path
    db_path = Path(__file__).parent / "trading_simulator.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT id, username, email, is_admin FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ User '{username}' not found in database")
            conn.close()
            return False
        
        user_id, username, email, is_admin = user
        
        if is_admin:
            print(f"ℹ️  User '{username}' is already an admin")
            conn.close()
            return True
        
        # Update user to admin
        cursor.execute("""
            UPDATE users 
            SET is_admin = 1, is_active = 1, is_verified = 1
            WHERE username = ?
        """, (username,))
        
        conn.commit()
        
        print(f"✅ Successfully granted admin privileges to user '{username}'")
        print(f"   User ID: {user_id}")
        print(f"   Email: {email}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python make_user_admin.py <username>")
        print("Example: python make_user_admin.py ayoubb")
        sys.exit(1)
    
    username = sys.argv[1]
    success = make_user_admin(username)
    sys.exit(0 if success else 1)
