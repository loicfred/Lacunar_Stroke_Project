#!/usr/bin/env python3
"""
Quick test to verify database and auth connection
"""
import sys
import os

# Add the correct path to import database.py from src/model/
current_dir = os.path.dirname(os.path.abspath(__file__))
# Go up: tests -> project root -> src -> model
project_root = os.path.dirname(current_dir)  # Lacunar_Stroke_Project
src_model_path = os.path.join(project_root, 'src', 'model')
sys.path.insert(0, src_model_path)

print(f"📁 Project root: {project_root}")
print(f"📁 Looking for database.py in: {src_model_path}")

try:
    from database import get_connection
    print("✅ Successfully imported database module")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n📂 Available files in src/model/:")
    if os.path.exists(src_model_path):
        for file in os.listdir(src_model_path):
            print(f"  - {file}")
    else:
        print(f"Directory not found: {src_model_path}")
        # Try to find it
        print("\n🔍 Searching for database.py...")
        for root, dirs, files in os.walk(project_root):
            if 'database.py' in files:
                print(f"Found database.py at: {root}")
                sys.path.insert(0, root)
    sys.exit(1)

def test_connection():
    print("\n🔌 Testing database connection...")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user table exists
        cursor.execute("SHOW TABLES LIKE 'user'")
        user_table = cursor.fetchone()

        if user_table:
            print("✅ User table exists")

            # Check columns
            cursor.execute("SHOW COLUMNS FROM `user`")
            columns = [col[0] for col in cursor.fetchall()]
            print(f"📋 User table columns: {', '.join(columns)}")

            # Check if password column exists
            if 'password' not in columns:
                print("❌ WARNING: 'password' column missing in user table!")
                print("   Run this SQL to fix:")
                print("   ALTER TABLE `user` ADD COLUMN password VARCHAR(255) NOT NULL;")

            # Check existing users
            cursor.execute("SELECT * FROM `user`")
            users = cursor.fetchall()
            print(f"👥 Total users found: {len(users)}")

            if users:
                print("📝 Sample users:")
                for user in users[:3]:  # Show first 3 users
                    print(f"  - ID: {user[0]}, Email: {user[1] if len(user) > 1 else 'N/A'}, Role: {user[3] if len(user) > 3 else 'N/A'}")

        else:
            print("❌ User table not found")
            print("\n💡 Creating user table...")

            # Create user table if it doesn't exist
            create_table_sql = """
                               CREATE TABLE IF NOT EXISTS `user` (
                                                                     id INT PRIMARY KEY AUTO_INCREMENT,
                                                                     email VARCHAR(255) UNIQUE NOT NULL,
                                                                     password VARCHAR(255) NOT NULL,
                                                                     role VARCHAR(50) DEFAULT 'patient',
                                                                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                               ); \
                               """

            cursor.execute(create_table_sql)
            conn.commit()
            print("✅ User table created successfully!")

        # Check other important tables
        print("\n📊 Checking other tables...")
        tables_to_check = ['patient_info', 'doctor_info', 'reading', 'notification']

        for table in tables_to_check:
            cursor.execute(f"SHOW TABLES LIKE '{table}'")
            exists = cursor.fetchone()
            print(f"  {table}: {'✅ Exists' if exists else '❌ Missing'}")

        cursor.close()
        conn.close()
        print("\n✅ Database connection successful!")

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 LACUNAR STROKE DATABASE CONNECTION TEST")
    print("=" * 60)

    if test_connection():
        print("\n" + "=" * 60)
        print("🎉 Database connection test PASSED!")
        print("\n📋 Next steps:")
        print("1. Run: python app.py")
        print("2. Visit: http://localhost:5000/register")
        print("3. Create your account")
        print("4. Login at: http://localhost:5000/login")
        print("5. Check your dashboard")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ Database connection test FAILED!")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check if database server is running")
        print("2. Verify database credentials in database.py")
        print("3. Check network connection to remote server")
        print("4. Ensure you have proper permissions")
        print("=" * 60)
        sys.exit(1)