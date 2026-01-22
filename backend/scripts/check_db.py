"""
Database check script
Verify if ChatMessage table exists and check database structure
"""
import sqlite3
import os

def check_database():
    """Check database structure"""
    db_path = os.path.join(os.path.dirname(__file__), "trading_platform.db")
    
    if not os.path.exists(db_path):
        print(f"❌ Database file not found: {db_path}")
        return
    
    print(f"✅ Database file found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    print("\n📋 Database Tables:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    
    # Check if chat_messages table exists
    print("\n🔍 Checking chat_messages table...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages';")
    chat_table = cursor.fetchone()
    
    if chat_table:
        print("✅ chat_messages table exists!")
        
        # Get table structure
        cursor.execute("PRAGMA table_info(chat_messages);")
        columns = cursor.fetchall()
        print("\n📊 Table Structure:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Count messages
        cursor.execute("SELECT COUNT(*) FROM chat_messages;")
        count = cursor.fetchone()[0]
        print(f"\n💬 Messages in database: {count}")
        
    else:
        print("❌ chat_messages table NOT found!")
        print("   The table needs to be created.")
        print("   Run: python init_db.py")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Database Check")
    print("=" * 60)
    check_database()
    print("\n" + "=" * 60)
