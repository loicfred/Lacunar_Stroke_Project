class PatientDetails:
    def __init__(self, patient_id, age_group, sex, hypertension, diabetes, smoking_history):
        self.patient_id = patient_id
        self.age_group = age_group
        self.sex = sex
        self.hypertension = hypertension
        self.diabetes = diabetes
        self.smoking_history = smoking_history
        self.first_name = None
        self.last_name = None