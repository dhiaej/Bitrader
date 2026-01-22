"""
Script to create or promote a user to admin
Run this script to set a user as admin in SQLite database
"""

import sqlite3
import sys
import os

# Get the database path
db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trading_simulator.db")

def list_users():
    """List all users in the database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, email, is_admin, is_active FROM users")
    users = cursor.fetchall()
    
    print("\n📋 Current Users:")
    print("-" * 80)
    print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Admin':<8} {'Active':<8}")
    print("-" * 80)
    
    for user in users:
        admin_status = "✅ Yes" if user[3] else "❌ No"
        active_status = "✅ Yes" if user[4] else "❌ No"
        print(f"{user[0]:<5} {user[1]:<20} {user[2]:<30} {admin_status:<8} {active_status:<8}")
    
    conn.close()
    return users

def promote_to_admin(username=None, user_id=None):
    """Promote a user to admin by username or user_id"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    if username:
        cursor.execute("SELECT id, username, is_admin FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        if not user:
            print(f"❌ User '{username}' not found!")
            conn.close()
            return False
        
        user_id = user[0]
        current_admin = user[2]
        
        if current_admin:
            print(f"✅ User '{username}' is already an admin!")
            conn.close()
            return True
        
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        conn.commit()
        print(f"✅ Successfully promoted '{username}' (ID: {user_id}) to admin!")
        
    elif user_id:
        cursor.execute("SELECT username, is_admin FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            print(f"❌ User with ID {user_id} not found!")
            conn.close()
            return False
        
        username = user[0]
        current_admin = user[1]
        
        if current_admin:
            print(f"✅ User '{username}' (ID: {user_id}) is already an admin!")
            conn.close()
            return True
        
        cursor.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
        conn.commit()
        print(f"✅ Successfully promoted '{username}' (ID: {user_id}) to admin!")
    
    conn.close()
    return True

def main():
    print("=" * 80)
    print("🔐 Admin User Setup Script")
    print("=" * 80)
    
    # List all users first
    users = list_users()
    
    if not users:
        print("\n❌ No users found in database. Please register a user first.")
        return
    
    print("\n" + "=" * 80)
    print("Options:")
    print("1. Promote user by username")
    print("2. Promote user by ID")
    print("3. Exit")
    print("=" * 80)
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        username = input("\nEnter username to promote: ").strip()
        if username:
            promote_to_admin(username=username)
        else:
            print("❌ Username cannot be empty!")
    
    elif choice == "2":
        try:
            user_id = int(input("\nEnter user ID to promote: ").strip())
            promote_to_admin(user_id=user_id)
        except ValueError:
            print("❌ Invalid user ID! Please enter a number.")
    
    elif choice == "3":
        print("\n👋 Exiting...")
        return
    
    else:
        print("❌ Invalid choice!")
        return
    
    # Show updated list
    print("\n" + "=" * 80)
    print("📋 Updated User List:")
    list_users()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Script interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

