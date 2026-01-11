import json

with open("patient.json", "r") as f:
    data = json.load(f)

class Patient:
    def __init__(self, patient_id, age_group, sex, hypertension, diabetes, smoking_history, left_sensory_score, right_sensory_score, asymmetry_index, affected_side, severity, asymmetry_label):
        self.patient_id = patient_id
        self.age_group = age_group
        self.sex = sex
        self.hypertension = hypertension
        self.diabetes = diabetes
        self.smoking_history = smoking_history
        self.left_sensory_score = left_sensory_score
        self.right_sensory_score = right_sensory_score
        self.asymmetry_index = asymmetry_index
        self.affected_side = affected_side
        self.severity = severity
        self.asymmetry_label = asymmetry_label

    @staticmethod
    def get(a, b):
        return a + b