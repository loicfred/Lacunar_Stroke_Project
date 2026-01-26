class Detailed_Reading:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.patient_id = kwargs.get("patient_id")
        self.timestamp = kwargs.get("timestamp")
        self.systolic_bp = kwargs.get("systolic_bp")
        self.diastolic_bp = kwargs.get("diastolic_bp")  # NEW
        self.hba1c = kwargs.get("hba1c")
        self.blood_glucose = kwargs.get("blood_glucose")  # NEW
        self.diabetes_type = kwargs.get("diabetes_type")  # NEW
        self.bp_category = kwargs.get("bp_category")  # NEW
        self.on_bp_medication = kwargs.get("on_bp_medication")  # NEW

        self.left_sensory_score = kwargs.get("left_sensory_score")
        self.right_sensory_score = kwargs.get("right_sensory_score")
        self.asymmetry_difference = kwargs.get("asymmetry_difference")
        self.average_asymmetry = kwargs.get("average_asymmetry")
        self.asymmetry_index = kwargs.get("asymmetry_index")
        self.risk_label = kwargs.get("risk_label")


