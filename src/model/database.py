import mariadb

from model.db.User import User
from model.db.Detailed_Report import Detailed_Report
from model.db.Notification import Notification
from model.db.Patient_Info import Patient_Info
from model.db.Reading import Reading

_conn = None
def get_connection():
    global _conn
    if _conn is None:
        _conn = mariadb.connect(
            user="Lacunar",
            password="LacunarStroke1234",
            host="54.37.40.206",
            port=3306,
            database="lacunar_stroke"
        )
    return _conn

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
    cursor.execute(f"SELECT * FROM {table_name.lower()} WHERE id = ?", entity_id)
    row = cursor.fetchone()
    if not row: return None
    entity_class = ENTITY_REGISTRY[table_name.lower()]
    return entity_class(**row)

def getAll(table_name):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name.lower()}")
    rows = cursor.fetchall()
    if not rows:
        return []
    entity_class = ENTITY_REGISTRY[table_name.lower()]
    return [entity_class(**row) for row in rows]


print(getByID('user', 1))
print(getByID('detailed_report', 1))