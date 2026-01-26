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

def get_connection():
    return mariadb.connect(
        user="Lacunar",
        password="LacunarStroke1234",
        host="54.37.40.206",
        port=3306,
        database="lacunar_stroke"
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
        columns = ", ".join(attributes.keys())
        placeholders = ", ".join(["?" for _ in attributes])
        query = f"INSERT INTO {table_name.lower()} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, tuple(attributes.values()))
        conn.commit()
        return cursor.lastrowid
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
            SELECT AVG(left_sensory_score) as avg_left, AVG(right_sensory_score) as avg_right
            FROM reading
            WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 10 
            """
        cursor.execute(query, (patient_id,))
        baseline = cursor.fetchone()
        return baseline if baseline['avg_left'] else {"avg_left": 10.0, "avg_right": 10.0}
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
                SELECT timestamp, left_sensory_score, right_sensory_score
                FROM reading
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


def get_recent_readings(patient_id, limit=5):
    """
    Fetches the most recent readings for volatility calculation.
    Required for identifying the 'stuttering pattern' of lacunar strokes.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
                SELECT left_sensory_score, right_sensory_score, timestamp
                FROM reading
                WHERE patient_id = ?
                ORDER BY timestamp DESC
                    LIMIT ? \
                """
        cursor.execute(query, (patient_id, limit))
        return cursor.fetchall()
    finally:
        conn.close()


def calculate_volatility_index(patient_id):
    """
    Calculates the standard deviation of the last 5 readings (Ref 3).
    High volatility + Downward trend = High probability of active stroke.
    """
    readings = get_recent_readings(patient_id, limit=5)

    if len(readings) < 2:
        return 0.0

    # Use the 'worst' side score for each reading to track neurological stability
    scores = [min(float(r['left_sensory_score']), float(r['right_sensory_score'])) for r in readings]

    # Biological volatility calculation using NumPy
    return round(float(np.std(scores)), 3)


def generate_sample_data():
    """
    Updated to use Gaussian distributions (Ref 1),
    Continuous Systolic BP (Ref 5), and HbA1c (Ref 6).
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

        patient_info = Patient_Info(
            id=user_id,
            age_group=random.choice(["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]),
            sex=random.choice(["Male", "Female"]),
            smoking_history=random.choice([0, 1]),
            first_name=f"Patient_{i}",
            last_name=f"Test_{i}"
            #doctor_id=None,               Added (optional)
            #notes=f"Sample patient {i}"   Added (optional)
        )
        insert("patient_info", patient_info)

        # Ref 5 & 6: Continuous Vital Mapping
        is_hypertensive = random.random() < 0.3
        is_diabetic = random.random() < 0.2

        # Gaussian distribution for BP and HbA1c
        base_systolic_bp = int(random.gauss(165, 15)) if is_hypertensive else int(random.gauss(122, 10))
        base_hba1c = round(random.gauss(7.8, 1.2), 1) if is_diabetic else round(random.gauss(5.2, 0.3), 1)

        # Ref 1: Gaussian Biological Data (Mean 9.0 for healthy)
        base_left = random.gauss(9.0, 0.5)
        base_right = random.gauss(9.0, 0.5)

        for x in range(10):
            noise_l = random.normalvariate(0, 0.3)
            noise_r = random.normalvariate(0, 0.3)

            current_systolic_bp = base_systolic_bp + random.uniform(-5, 5)
            current_hba1c = base_hba1c + random.uniform(-0.3, 0.3)

            reading = Reading(
                patient_id=user_id,
                timestamp=datetime.now() - timedelta(hours=((10-x)*3)),
                systolic_bp=current_systolic_bp,
                hba1c=current_hba1c,
                left_sensory_score=round(max(0, min(10, base_left + noise_l)), 2),
                right_sensory_score=round(max(0, min(10, base_right + noise_r)), 2)
            )

            # Simulate slight decline for some patients to create 'stuttering' history
            if i % 5 == 0: # 20% of sample patients have fluctuating/declining scores
                base_left -= random.uniform(0.1, 0.4)

            insert("reading", reading)

    print("\n✅ Successfully generated history with Volatility and Continuous health markers!")

def toCSV(itemlist, filename):
    master_df = pd.DataFrame([p.__dict__ for p in itemlist])
    master_df.to_csv(os.path.join("output", filename + ".csv"), index=False)


