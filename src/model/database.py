import mariadb
import random
import os
import pandas as pd

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

            return round(left_velocity, 3), round(right_velocity, 3), round(avg_time_diff, 2)

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

            return round(left_velocity, 3), round(right_velocity, 3), round(time_diff, 2)

    except Exception as e:
        print(f"Error calculating reading velocity: {e}")
        import traceback
        traceback.print_exc()
        return 0.0, 0.0, 0.0
    finally:
        if conn:
            conn.close()

def generate_sample_data():
    total_patients = 100
    print(f"🚀 Starting data generation for {total_patients} patients...")
    print("⚠️ Please wait, this may take several minutes due to remote database latency.")

    for i in range(total_patients):
        user = User(
            username=f"user_{i}_{random.randint(1000, 9999)}",
            email=f"user{i}@example.com",
            password=f"pass{random.randint(10000, 99999)}",
            role=random.choice(["PATIENT"])
        )
        user_id = insert("user", user)

        patient_info = Patient_Info(
            id=user_id,
            age_group=random.choice(["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]),
            sex=random.choice(["Male", "Female"]),
            diabetes=random.choice([0, 1]),
            smoking_history=random.choice([0, 1]),
        )
        patient_info.id = user_id
        insert("patient_info", patient_info)

        # Initial scores
        left_score = random.uniform(7, 10)
        right_score = random.uniform(7, 10)
        blood_pressure = random.uniform(80, 150)

        for x in range(10):
            reading = Reading(
                patient_id=user_id,
                timestamp=datetime.now() + timedelta(hours=(x*3)),
                blood_pressure=random.uniform(80, 150),
                left_sensory_score=round(left_score, 2),
                right_sensory_score=round(right_score, 2)
            )

            left_score = left_score + random.uniform(0.05, -0.5)
            right_score = right_score + random.uniform(0.05, -0.5)
            blood_pressure = blood_pressure + random.uniform(3, -3)
            reading.left_sensory_score = left_score
            reading.right_sensory_score = right_score
            reading.blood_pressure = blood_pressure

            insert("reading", reading)

        # PROGRESS BAR LOGIC: Print status every 10 patients
        if (i + 1) % 10 == 0:
            percent = int(((i + 1) / total_patients) * 100)
            print(f"⏳ Progress: {percent}% completed ({i + 1}/{total_patients} patients saved...)")

    print("\n✅ Successfully generated 100 sample records and their reading histories!")

def toCSV(itemlist, filename):
    master_df = pd.DataFrame([p.__dict__ for p in itemlist])
    master_df.to_csv(os.path.join("output", filename + ".csv"), index=False)


