#!/usr/bin/env python3
"""
Quick test to verify database and auth connection
"""
from database import get_connection
import sys

def test_connection():
    print("🔌 Testing database connection...")
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user table exists
        cursor.execute("SHOW TABLES LIKE 'user'")
        user_table = cursor.fetchone()

        if user_table:
            print("✅ User table exists")

            # Check columns
            cursor.execute("SHOW COLUMNS FROM user")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"📋 User table columns: {columns}")

            # Check existing users
            cursor.execute("SELECT COUNT(*) as count FROM user")
            count = cursor.fetchone()[0]
            print(f"👥 Total users in database: {count}")
        else:
            print("❌ User table not found")
            print("💡 Please run the SQL to create the user table:")
            print("""
                  CREATE TABLE user (
                                        id INT PRIMARY KEY AUTO_INCREMENT,
                                        email VARCHAR(255) UNIQUE NOT NULL,
                                        password VARCHAR(255) NOT NULL,
                                        role VARCHAR(50) DEFAULT 'patient',
                                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                  );
                  """)

        cursor.close()
        conn.close()
        print("✅ Database connection successful!")

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    if test_connection():
        print("\n🎉 Database connection test passed!")
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Visit: http://localhost:5000/login")
        print("3. Register as patient or doctor")
        print("4. Login and check dashboard")
    else:
        print("\n❌ Fix database connection first!")
        sys.exit(1)