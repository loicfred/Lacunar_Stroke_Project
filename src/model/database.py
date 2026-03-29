import mariadb
import random
import os
import pandas as pd
import numpy as np

from datetime import datetime, timedelta

from model.db.Detailed_Reading import Detailed_Reading
from model.db.Doctor_Info import Doctor_Info
from model.db.User import User
from model.db.Patient_Report import Patient_Report
from model.db.Notification import Notification
from model.db.Patient_Info import Patient_Info
from model.db.Reading import Reading

from dotenv import load_dotenv
load_dotenv()

def get_connection():
    return mariadb.connect(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME")
    )

ENTITY_REGISTRY = {
    "user": User,
    "patient_info": Patient_Info,
    "doctor_info": Doctor_Info,
    "reading": Reading,
    "detailed_reading": Detailed_Reading,
    "notification": Notification,
    "patient_report": Patient_Report,
}

def callProcedure(table_name, statement, *value):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"{statement.lower()}", value)
        rows = cursor.fetchall()
        if not rows: return []
        entity_class = ENTITY_REGISTRY[table_name.lower()]
        return [entity_class(**row) for row in rows]
    finally:
        conn.close()

def getByID(table_name, entity_id):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name.lower()} WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        if not row: return None
        entity_class = ENTITY_REGISTRY[table_name.lower()]
        return entity_class(**row)
    finally:
        conn.close()

def getWhere(table_name, condition, *value):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name.lower()} WHERE {condition}", value)
        row = cursor.fetchone()
        if not row: return None
        entity_class = ENTITY_REGISTRY[table_name.lower()]
        return entity_class(**row)
    finally:
        conn.close()

def getAll(table_name):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name.lower()}")
        rows = cursor.fetchall()
        if not rows: return []
        entity_class = ENTITY_REGISTRY[table_name.lower()]
        return [entity_class(**row) for row in rows]
    finally:
        conn.close()

def getAllWhere(table_name, condition, *value):
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM {table_name.lower()} WHERE {condition}", value)
        rows = cursor.fetchall()
        if not rows: return []
        entity_class = ENTITY_REGISTRY[table_name.lower()]
        return [entity_class(**row) for row in rows]
    finally:
        conn.close()

def insert(table_name, entity):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        attributes = {k: v for k, v in entity.__dict__.items() if v is not None}

        # If trying to insert into a view, redirect to the actual table
        if table_name.lower() == 'detailed_reading':
            print(f"⚠️ Redirecting insert from view 'detailed_reading' to actual table 'reading'")
            table_name = 'reading'

        # Check what columns actually exist in the table
        cursor.execute(f"SHOW COLUMNS FROM {table_name.lower()}")
        existing_columns = [col[0] for col in cursor.fetchall()]

        # Filter attributes to only include columns that exist
        filtered_attributes = {k: v for k, v in attributes.items() if k in existing_columns}

        if not filtered_attributes:
            raise ValueError(f"No valid attributes to insert into {table_name}")

        columns = ", ".join(filtered_attributes.keys())
        placeholders = ", ".join(["?" for _ in filtered_attributes])
        query = f"INSERT INTO {table_name.lower()} ({columns}) VALUES ({placeholders})"

        print(f"📝 Inserting into {table_name}: {list(filtered_attributes.keys())}")
        cursor.execute(query, tuple(filtered_attributes.values()))
        conn.commit()

        return cursor.lastrowid

    except Exception as e:
        print(f"❌ Error in insert: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def update(table_name, entity_id, fields):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        set_clause = ", ".join([f"{key} = ?" for key in fields.keys()])
        query = f"UPDATE {table_name.lower()} SET {set_clause} WHERE id = ?"
        cursor.execute(query, tuple(list(fields.values()) + [entity_id]))
        conn.commit()
        conn.close()
        return cursor.rowcount
    finally:
        conn.close()

def delete(table_name, entity_id):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        query = f"DELETE FROM {table_name.lower()} WHERE id = ?"
        cursor.execute(query, (entity_id,))
        conn.commit()
        conn.close()
        return cursor.rowcount
    finally:
        conn.close()

def get_patient_baseline(patient_id):
    """
    IMPROVEMENT: Calculates the average sensory scores for a patient
    from their last 10 readings to establish a 'Normal' baseline.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
                SELECT
                    AVG(left_sensory_score) as avg_left,
                    AVG(right_sensory_score) as avg_right,
                    AVG(systolic_bp) as avg_systolic,
                    AVG(diastolic_bp) as avg_diastolic,
                    AVG(hba1c) as avg_hba1c,
                    AVG(blood_glucose) as avg_blood_glucose,
                    AVG(volatility_index) as avg_volatility
                FROM detailed_reading
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                    LIMIT 10 \
                """
        cursor.execute(query, (patient_id,))
        baseline = cursor.fetchone()
        # Return with defaults if no data
        if not baseline or baseline['avg_left'] is None:
            return {
                "avg_left": 9.0, "avg_right": 9.0,
                "avg_systolic": 120, "avg_diastolic": 80,
                "avg_hba1c": 5.4, "avg_blood_glucose": 100,
                "avg_volatility": 0.3
            }
        return baseline
    finally:
        conn.close()


def get_reading_velocity(patient_id):
    """
    Calculate smoothed velocity using 5-point method for lacunar stroke detection.
    Returns: (left_velocity, right_velocity, time_diff_hours)
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # CHANGE 1: LIMIT 2 → LIMIT 5
        query = """
                SELECT timestamp, left_sensory_score, right_sensory_score,
                       systolic_bp, diastolic_bp, hba1c, blood_glucose,
                       volatility_index
                FROM detailed_reading
                WHERE patient_id = %s
                ORDER BY timestamp DESC
                    LIMIT 5
                """
        cursor.execute(query, (patient_id,))
        readings = cursor.fetchall()

        if len(readings) < 2:
            return 0.0, 0.0, 0.0

        # If we have 5 readings, use smart 5-point math
        if len(readings) >= 5:
            # Put readings in order: oldest to newest
            readings = list(reversed(readings))

            # Get scores as numbers
            left_scores = []
            right_scores = []
            timestamps = []

            for r in readings:
                left = float(r['left_sensory_score']) if r['left_sensory_score'] is not None else 0.0
                right = float(r['right_sensory_score']) if r['right_sensory_score'] is not None else 0.0
                left_scores.append(left)
                right_scores.append(right)
                timestamps.append(r['timestamp'])

            # 5-POINT FORMULA FOR LACUNAR STROKES:
            # Looks at pattern: score1, score2, score3, score4, score5
            # Detects "up-down-up-down" stuttering pattern
            left_velocity = (-left_scores[4] + 8*left_scores[3] - 8*left_scores[1] + left_scores[0]) / 12
            right_velocity = (-right_scores[4] + 8*right_scores[3] - 8*right_scores[1] + right_scores[0]) / 12

            # Calculate average time between readings
            time_diffs = []
            for i in range(1, len(timestamps)):
                diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600
                if diff > 0:
                    time_diffs.append(diff)

            avg_time_diff = sum(time_diffs)/len(time_diffs) if time_diffs else 1.0

            # Make velocity "per hour"
            left_velocity = left_velocity / avg_time_diff
            right_velocity = right_velocity / avg_time_diff

            return round(left_velocity, 6), round(right_velocity, 6), round(avg_time_diff, 2)

        else:
            # Fallback: 2-point method for 2-4 readings
            current = readings[0]
            previous = readings[1]

            current_left = float(current['left_sensory_score']) if current['left_sensory_score'] is not None else 0.0
            current_right = float(current['right_sensory_score']) if current['right_sensory_score'] is not None else 0.0
            previous_left = float(previous['left_sensory_score']) if previous['left_sensory_score'] is not None else 0.0
            previous_right = float(previous['right_sensory_score']) if previous['right_sensory_score'] is not None else 0.0

            time_diff = (current['timestamp'] - previous['timestamp']).total_seconds() / 3600
            if time_diff == 0:
                time_diff = 0.01

            left_velocity = (current_left - previous_left) / time_diff
            right_velocity = (current_right - previous_right) / time_diff

            return round(left_velocity, 6), round(right_velocity, 6), round(time_diff, 2)

    except Exception as e:
        print(f"Error calculating reading velocity: {e}")
        import traceback
        traceback.print_exc()
        return 0.0, 0.0, 0.0
    finally:
        if conn:
            conn.close()


def calculate_volatility_index(patient_id):
    """
    Calculates the standard deviation of the last 5 readings (Ref 3).
    High volatility + Downward trend = High probability of active stroke.
    """
    readings = getAllWhere('detailed_reading', 'patient_id = ? ORDER BY timestamp DESC LIMIT 5', patient_id)

    if len(readings) < 2:
        return 0.0

    # Use the 'worst' side score for each reading to track neurological stability
    scores = [min(float(r.left_sensory_score), float(r.right_sensory_score)) for r in readings]

    # Biological volatility calculation using NumPy
    return round(float(np.std(scores)), 3)


def get_recent_readings(patient_id, limit=5):
    """
    Fetches the most recent readings for pattern analysis.
    Works with both tables and views.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)  # Important: dictionary=True

        # Try 'reading' table first (the actual table)
        try:
            # Get columns from reading table
            cursor.execute("SHOW COLUMNS FROM reading")
            reading_columns = [col[0] for col in cursor.fetchall()]

            # Build query with available columns
            base_columns = ['id', 'patient_id', 'timestamp',
                            'left_sensory_score', 'right_sensory_score',
                            'systolic_bp', 'diastolic_bp', 'hba1c', 'blood_glucose',
                            'diabetes_type', 'bp_category', 'on_bp_medication']

            # Add optional columns if they exist
            optional_columns = ['asymmetry_index', 'score_velocity', 'volatility_index',
                                'pattern_volatility', 'pattern_velocity_trend',
                                'pattern_stuttering_score', 'pattern_amplitude',
                                'pattern_asymmetry_progression', 'pattern_type',
                                'pattern_consistency', 'pattern_reading_count',
                                'prediction_tier', 'risk_label', 'affected_side', 'model_confidence']

            select_columns = base_columns.copy()
            for col in optional_columns:
                if col in reading_columns:
                    select_columns.append(col)

            query = f"""
                    SELECT {', '.join(select_columns)}
                    FROM reading
                    WHERE patient_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """

            cursor.execute(query, (patient_id, limit))
            results = cursor.fetchall()

            if results:
                print(f"✅ Found {len(results)} readings from 'reading' table")
                return results

        except Exception as e:
            print(f"⚠️ Could not fetch from reading table: {e}")

        # Fallback to detailed_reading view
        try:
            print("⚠️ Falling back to detailed_reading view")
            cursor.execute("""
                           SELECT id, patient_id, timestamp,
                                  left_sensory_score, right_sensory_score,
                                  systolic_bp, diastolic_bp, hba1c, blood_glucose,
                                  diabetes_type, bp_category, on_bp_medication
                           FROM detailed_reading
                           WHERE patient_id = ?
                           ORDER BY timestamp DESC
                               LIMIT ?
                           """, (patient_id, limit))
            results = cursor.fetchall()
            print(f"✅ Found {len(results)} readings from 'detailed_reading' view")
            return results

        except Exception as e:
            print(f"⚠️ Could not fetch from detailed_reading view: {e}")
            return []

    except Exception as e:
        print(f"Error fetching recent readings: {e}")
        return []
    finally:
        conn.close()


def generate_sample_data():
    """
    Updated to use Gaussian distributions (Ref 1),
    Continuous Systolic BP (Ref 5), and HbA1c (Ref 6).
    Now includes all new fields for comprehensive stroke risk assessment.
    """
    total_patients = 100
    print(f"🚀 Starting data generation with Gaussian/Continuous biological logic...")

    for i in range(total_patients):
        user = User(
            username=f"user_{i}_{random.randint(1000, 9999)}",
            email=f"user{i}@example.com",
            password="password123",
            role="PATIENT"
        )
        user_id = insert("user", user)

        # Generate patient conditions
        has_hypertension = random.random() < 0.3
        has_diabetes = random.random() < 0.2
        # BP medication with 3 options
        if has_hypertension:
            on_bp_meds = random.choices([1, 2, 0], weights=[0.6, 0.2, 0.2])[0]  # 1=Yes, 2=Irregular, 0=No
        else:
            on_bp_meds = random.choices([0, 2, 1], weights=[0.85, 0.1, 0.05])[0]

        # Determine diabetes type if diabetic
        diabetes_type = "None"
        if has_diabetes:
            diabetes_type = random.choices(
                ["Type 1", "Type 2", "Prediabetes", "Gestational"],
                weights=[0.1, 0.7, 0.15, 0.05]
            )[0]

        patient_info = Patient_Info(
            id=user_id,
            age_group=random.choice(["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]),
            sex=random.choice(["Male", "Female"]),
            smoking_history=random.choice([0, 1]),
            first_name=f"Patient_{i}",
            last_name=f"Test_{i}",
            doctor_id=1,
            notes=f"Patient {i} notes"
        )
        insert("patient_info", patient_info)

        # Gaussian distribution for BP and HbA1c
        if has_hypertension:
            base_systolic_bp = int(random.gauss(145, 15))
            base_diastolic_bp = int(random.gauss(95, 10))
            bp_category = random.choices(
                ["Hypertension Stage 1", "Hypertension Stage 2"],
                weights=[0.6, 0.4]
            )[0]
        else:
            base_systolic_bp = int(random.gauss(118, 8))
            base_diastolic_bp = int(random.gauss(78, 5))
            bp_category = "Normal" if random.random() < 0.7 else "Elevated"

        # Blood glucose based on diabetes status
        if has_diabetes:
            base_hba1c = round(random.gauss(7.5, 1.0), 1)
            base_blood_glucose = int(random.gauss(180, 40))
        else:
            base_hba1c = round(random.gauss(5.2, 0.3), 1)
            base_blood_glucose = int(random.gauss(100, 15))

        # Ref 1: Gaussian Biological Data (Mean 9.0 for healthy)
        base_left = random.gauss(9.0, 0.5)
        base_right = random.gauss(9.0, 0.5)

        previous_left = base_left
        previous_right = base_right

        for x in range(10):
            # Add biological noise
            noise_l = random.normalvariate(0, 0.3)
            noise_r = random.normalvariate(0, 0.3)

            # Vary vital signs slightly each reading
            current_systolic_bp = max(90, min(220, base_systolic_bp + random.uniform(-8, 8)))
            current_diastolic_bp = max(60, min(130, base_diastolic_bp + random.uniform(-5, 5)))
            current_hba1c = max(4.0, min(14.0, base_hba1c + random.uniform(-0.2, 0.2)))
            current_blood_glucose = max(70, min(500, base_blood_glucose + random.randint(-20, 20)))

            # Calculate current sensory scores with potential decline
            current_left = round(max(0, min(10, previous_left + noise_l)), 2)
            current_right = round(max(0, min(10, previous_right + noise_r)), 2)

            # Calculate derived metrics
            avg_score = (current_left + current_right) / 2
            asymmetry_index = abs(current_left - current_right) / (avg_score + 1)

            # Simulate velocity for some patients
            score_velocity = 0.0
            if x > 0:
                # Some patients show decline (simulating stroke progression)
                if i % 7 == 0:  # ~14% show decline
                    decline_rate = random.uniform(-0.05, -0.01)
                    current_left = max(0, current_left + decline_rate)
                    current_right = max(0, current_right + decline_rate)

            # Calculate volatility from recent trend
            volatility_index = random.uniform(0.1, 0.5)  # Base volatility

            # For stroke patients, higher volatility
            if i % 10 == 0:  # 10% are simulated stroke patients
                volatility_index = random.uniform(1.5, 2.5)
                # More asymmetric scores for stroke patients
                if random.random() < 0.7:
                    asymmetry_factor = random.uniform(0.3, 1.5)
                    if random.choice([True, False]):
                        current_left = max(0, current_left - asymmetry_factor)
                    else:
                        current_right = max(0, current_right - asymmetry_factor)

            reading = Reading(
                patient_id=user_id,
                timestamp=datetime.now() - timedelta(hours=((10-x)*3)),
                systolic_bp=current_systolic_bp,
                diastolic_bp=current_diastolic_bp,
                hba1c=current_hba1c,
                blood_glucose=current_blood_glucose,
                diabetes_type=diabetes_type,
                bp_category=bp_category,
                on_bp_medication=on_bp_meds,
                left_sensory_score=current_left,
                right_sensory_score=current_right,
                asymmetry_index=round(asymmetry_index, 3),
                score_velocity=round(score_velocity, 6),
                volatility_index=round(volatility_index, 3)
            )

            # Update for next iteration
            previous_left = current_left
            previous_right = current_right

            insert("reading", reading)

    print("\n✅ Successfully generated history with all 13 features for comprehensive stroke assessment!")

def toCSV(itemlist, filename):
    master_df = pd.DataFrame([p.__dict__ for p in itemlist])
    master_df.to_csv(os.path.join("output", filename + ".csv"), index=False)


