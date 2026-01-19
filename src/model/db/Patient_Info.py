class Patient_Info:
    def __init__(self, **kwargs):
        self.id = kwargs.get("patient_id")
        self.age_group = kwargs.get("age_group")
        self.sex = kwargs.get("sex")
        self.hypertension = kwargs.get("hypertension")
        self.diabetes = kwargs.get("diabetes")
        self.smoking_history = kwargs.get("smoking_history")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")
        self.doctor_id = kwargs.get("doctor_id")