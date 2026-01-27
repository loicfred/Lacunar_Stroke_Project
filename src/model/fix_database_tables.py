import mariadb

def fix_database_tables():
    """Add missing columns to the actual tables, not the view."""

    try:
        # Connect to database
        conn = mariadb.connect(
            user="Lacunar",
            password="LacunarStroke1234",
            host="54.37.40.206",
            port=3306,
            database="lacunar_stroke"
        )

        cursor = conn.cursor()

        print("🔧 Fixing database tables (not views)...")

        # Only fix actual tables, not views
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")
        tables = [row[0] for row in cursor.fetchall()]

        print(f"Found tables: {tables}")

        columns_to_add = [
            ('asymmetry_index', 'FLOAT DEFAULT 0.0'),
            ('score_velocity', 'FLOAT DEFAULT 0.0'),
            ('volatility_index', 'FLOAT DEFAULT 0.0'),
            ('pattern_volatility', 'FLOAT DEFAULT 0.0'),
            ('pattern_velocity_trend', 'FLOAT DEFAULT 0.0'),
            ('pattern_stuttering_score', 'INT DEFAULT 0'),
            ('pattern_amplitude', 'FLOAT DEFAULT 0.0'),
            ('pattern_asymmetry_progression', 'FLOAT DEFAULT 0.0'),
            ('pattern_type', 'INT DEFAULT 0'),
            ('pattern_consistency', 'FLOAT DEFAULT 0.0'),
            ('pattern_reading_count', 'INT DEFAULT 5')
        ]

        for table in tables:
            try:
                # Skip if not reading-related
                if 'reading' not in table.lower():
                    continue

                print(f"\n📊 Table: {table}")

                # Get existing columns
                cursor.execute(f"SHOW COLUMNS FROM {table}")
                existing_columns = [col[0] for col in cursor.fetchall()]

                # Add missing columns
                for col_name, col_def in columns_to_add:
                    if col_name not in existing_columns:
                        print(f"  ➕ Adding column: {col_name}")
                        try:
                            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_def}")
                            print(f"    ✅ Added successfully")
                        except mariadb.Error as e:
                            print(f"    ⚠️ Could not add {col_name}: {e}")
                    else:
                        print(f"  ✓ Column '{col_name}' already exists")

            except mariadb.Error as e:
                print(f"  ❌ Error processing table '{table}': {e}")

        conn.commit()
        print("\n✅ Database tables updated successfully!")

        # Show final schema
        print("\n📋 Final schema for tables:")
        for table in tables:
            if 'reading' in table.lower():
                print(f"\n{table}:")
                cursor.execute(f"DESCRIBE {table}")
                for col in cursor.fetchall():
                    print(f"  {col[0]:30} {col[1]:20}")

        conn.close()

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        import traceback
        traceback.print_exc()

def check_views():
    """Check what views exist and their definitions."""

    try:
        conn = mariadb.connect(
            user="Lacunar",
            password="LacunarStroke1234",
            host="54.37.40.206",
            port=3306,
            database="lacunar_stroke"
        )

        cursor = conn.cursor()

        print("\n🔍 Checking views...")

        # Get all views
        cursor.execute("SHOW FULL TABLES WHERE Table_type = 'VIEW'")
        views = [(row[0], 'VIEW') for row in cursor.fetchall()]

        for view_name, _ in views:
            print(f"\n📋 View: {view_name}")

            # Get view definition
            cursor.execute(f"SHOW CREATE VIEW {view_name}")
            result = cursor.fetchone()
            if result:
                print(f"Definition:\n{result[1]}")

            # Check columns in view
            cursor.execute(f"SHOW COLUMNS FROM {view_name}")
            columns = cursor.fetchall()
            print(f"Columns ({len(columns)}): {[col[0] for col in columns]}")

        conn.close()

    except Exception as e:
        print(f"Error checking views: {e}")

if __name__ == "__main__":
    fix_database_tables()
    check_views()