import mariadb

def test_direct_insert():
    """Test inserting directly into the database to bypass view issues."""

    try:
        conn = mariadb.connect(
            user="Lacunar",
            password="LacunarStroke1234",
            host="54.37.40.206",
            port=3306,
            database="lacunar_stroke"
        )

        cursor = conn.cursor()

        # Check what tables exist
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Available tables: {tables}")

        # Check reading table structure
        if 'reading' in tables:
            cursor.execute("DESCRIBE reading")
            columns = cursor.fetchall()
            print("\n📋 'reading' table columns:")
            for col in columns:
                print(f"  {col[0]:30} {col[1]:20} {col[2]}")

        # Try a simple insert
        test_data = {
            'patient_id': 1,
            'left_sensory_score': 8.5,
            'right_sensory_score': 7.8,
            'systolic_bp': 135,
            'diastolic_bp': 80,
            'hba1c': 5.8,
            'blood_glucose': 100,
            'diabetes_type': 'None',
            'bp_category': 'Normal',
            'on_bp_medication': 0
        }

        # Build insert query with only basic columns
        columns = list(test_data.keys())
        values = list(test_data.values())
        placeholders = ', '.join(['%s'] * len(values))

        query = f"INSERT INTO reading ({', '.join(columns)}) VALUES ({placeholders})"

        print(f"\n📝 Test insert query: {query}")

        cursor.execute(query, values)
        conn.commit()

        print(f"✅ Test insert successful! Row ID: {cursor.lastrowid}")

        conn.close()

    except Exception as e:
        print(f"❌ Test insert failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_direct_insert()