class PatientDetails:
    def __init__(self, patient_id, age_group, sex, systolic_bp, diastolic_bp,
                 hba1c, blood_glucose, diabetes_type, bp_category, on_bp_medication,
                 smoking_history):
        self.patient_id = patient_id
        self.age_group = age_group
        self.sex = sex
        self.systolic_bp = systolic_bp
        self.diastolic_bp = diastolic_bp  # NEW
        self.hba1c = hba1c
        self.blood_glucose = blood_glucose  # NEW
        self.diabetes_type = diabetes_type  # NEW
        self.bp_category = bp_category  # NEW
        self.on_bp_medication = on_bp_medication  # NEW
        self.smoking_history = smoking_history