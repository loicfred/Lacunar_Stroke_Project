from src.model.db.database import get_connection, getAll
from src.model.User import User
from werkzeug.security import generate_password_hash, check_password_hash

def test_auth_integration():
    """Test that our auth system works with existing database"""
    print("🧪 Testing authentication integration...")
    print("=" * 60)

    # 1. Test database connection
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT VERSION() as version")
        version = cursor.fetchone()['version']
        cursor.close()
        conn.close()
        print(f"✅ Database connection successful (MariaDB {version})")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return

    # 2. Check user table structure
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW COLUMNS FROM user")  # Note: table is "user" not "users"
        columns = [col['Field'] for col in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"📋 User table columns: {columns}")

        # Check for required columns
        required_columns = ['id', 'email', 'password', 'role']
        missing_columns = [col for col in required_columns if col not in columns]

        if missing_columns:
            print(f"❌ Missing columns in user table: {missing_columns}")
            print("   Please run these SQL commands:")
            if 'password' in missing_columns:
                print("   ALTER TABLE user ADD COLUMN password VARCHAR(255) NOT NULL;")
            if 'role' in missing_columns:
                print("   ALTER TABLE user ADD COLUMN role VARCHAR(50) DEFAULT 'patient';")
        else:
            print("✅ All required columns present in user table")

    except Exception as e:
        print(f"❌ Error checking table structure: {e}")

    # 3. Test password hashing
    print("\n🔐 Testing password hashing...")
    test_password = "test123"
    hashed_password = generate_password_hash(test_password)

    print(f"   Original password: {test_password}")
    print(f"   Hashed password: {hashed_password[:50]}...")

    # Test password verification
    is_valid = check_password_hash(hashed_password, test_password)
    print(f"   Password verification: {'✅ PASS' if is_valid else '❌ FAIL'}")

    # 4. Test existing getAll function
    try:
        users = getAll("user")
        print(f"\n👥 Found {len(users)} existing users in database")

        if users:
            print("   Sample user data:")
            for i, user in enumerate(users[:3]):  # Show first 3 users
                if hasattr(user, 'email'):
                    print(f"   {i+1}. ID: {user.id}, Email: {user.email}, Role: {getattr(user, 'role', 'N/A')}")
    except Exception as e:
        print(f"❌ Error getting users: {e}")

    # 5. Check if patient_info table exists and matches user IDs
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SHOW COLUMNS FROM patient_info")
        patient_columns = [col['Field'] for col in cursor.fetchall()]
        cursor.close()
        conn.close()

        print(f"\n🏥 Patient_info table columns: {patient_columns}")

        if 'id' in patient_columns:
            print("✅ Patient_info table has id column (should match user.id)")
        else:
            print("❌ Patient_info table missing id column")

    except Exception as e:
        print(f"❌ Error checking patient_info table: {e}")

    print("\n" + "=" * 60)
    print("🎯 GREEN team authentication test complete!")

if __name__ == "__main__":
    test_auth_integration()