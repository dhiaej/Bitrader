"""
Check Users Script
Display all users in the database with their admin status
"""
import sqlite3
from pathlib import Path
from tabulate import tabulate

def check_users():
    """Display all users with their details"""
    
    # Get the database path
    db_path = Path(__file__).parent / "trading_simulator.db"
    
    if not db_path.exists():
        print(f"❌ Database not found at: {db_path}")
        return
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("""
            SELECT 
                id, 
                username, 
                email, 
                is_admin, 
                is_active, 
                is_verified,
                created_at
            FROM users 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("No users found in database")
            conn.close()
            return
        
        # Format data for display
        headers = ["ID", "Username", "Email", "Admin", "Active", "Verified", "Created"]
        rows = []
        
        for user in users:
            user_id, username, email, is_admin, is_active, is_verified, created_at = user
            rows.append([
                user_id,
                username,
                email[:30] + "..." if len(email) > 30 else email,
                "✅" if is_admin else "❌",
                "✅" if is_active else "❌",
                "✅" if is_verified else "❌",
                created_at[:10] if created_at else "N/A"
            ])
        
        print("\n" + "="*100)
        print("USERS IN DATABASE")
        print("="*100)
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        print(f"\nTotal Users: {len(users)}")
        print(f"Admins: {sum(1 for u in users if u[3])}")
        print(f"Active: {sum(1 for u in users if u[4])}")
        print("="*100 + "\n")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_users()
