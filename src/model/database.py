import mariadb
import random
import os
import pandas as pd

from datetime import datetime, timedelta
from model.db.User import User
from model.db.Detailed_Report import Detailed_Report
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
    "patient": Patient_Info,
    "reading": Reading,
    "detailed_report": Detailed_Report,
    "notification": Notification
}

def getByID(table_name, entity_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name.lower()} WHERE id = ?", (entity_id,))
    row = cursor.fetchone()
    if not row: return None
    entity_class = ENTITY_REGISTRY[table_name.lower()]
    conn.close()
    return entity_class(**row)

def getAll(table_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name.lower()}")
    rows = cursor.fetchall()
    if not rows: return []
    entity_class = ENTITY_REGISTRY[table_name.lower()]
    conn.close()
    return [entity_class(**row) for row in rows]

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
    IMPROVEMENT: Calculates the change in score and time since the last reading.
    Returns: (left_delta, right_delta, hours_passed)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Get the two most recent readings
        query = """
            SELECT left_sensory_score, right_sensory_score, timestamp
            FROM reading
            WHERE patient_id = ?
            ORDER BY timestamp DESC LIMIT 2 \
            """
        cursor.execute(query, (patient_id,))
        rows = cursor.fetchall()

        if len(rows) < 2:
            return 0.0, 0.0, 0.0 # Not enough history to calculate velocity

        current, previous = rows[0], rows[1]

        # Calculate time difference in hours
        time_diff = (current['timestamp'] - previous['timestamp']).total_seconds() / 3600
        if time_diff == 0: time_diff = 0.01 # Avoid division by zero

        # Calculate rate of change per hour
        left_velocity = (current['left_sensory_score'] - previous['left_sensory_score']) / time_diff
        right_velocity = (current['right_sensory_score'] - previous['right_sensory_score']) / time_diff

        return round(left_velocity, 3), round(right_velocity, 3), round(time_diff, 2)
    finally:
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
            role=random.choice(["USER"])
        )
        user_id = insert("user", user)

        patient_info = Patient_Info(
            id=user_id,
            age_group=random.choice(["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]),
            sex=random.choice(["Male", "Female"]),
            hypertension=random.choice([0, 1]),
            diabetes=random.choice([0, 1]),
            smoking_history=random.choice([0, 1]),
        )
        patient_info.id = user_id
        insert("patient_info", patient_info)

        # Initial scores
        left_score = random.uniform(7, 10)
        right_score = random.uniform(7, 10)

        for x in range(10):
            reading = Reading(
                patient_id=user_id,
                timestamp=datetime.now() + timedelta(hours=(x*3)),
                left_sensory_score=round(left_score, 2),
                right_sensory_score=round(right_score, 2)
            )

            left_score = left_score + random.uniform(0.05, -0.5)
            right_score = right_score + random.uniform(0.05, -0.5)
            reading.left_sensory_score = left_score
            reading.right_sensory_score = right_score

            insert("reading", reading)

        # PROGRESS BAR LOGIC: Print status every 10 patients
        if (i + 1) % 10 == 0:
            percent = int(((i + 1) / total_patients) * 100)
            print(f"⏳ Progress: {percent}% completed ({i + 1}/{total_patients} patients saved...)")

    print("\n✅ Successfully generated 100 sample records and their reading histories!")

def toCSV(itemlist, filename):
    master_df = pd.DataFrame([p.__dict__ for p in itemlist])
    master_df.to_csv(os.path.join("output", filename + ".csv"), index=False)


generate_sample_data()