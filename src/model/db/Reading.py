class Reading:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.patient_id = kwargs.get("patient_id")
        self.timestamp = kwargs.get("timestamp")
        self.systolic_bp = kwargs.get("systolic_bp")
        self.hba1c = kwargs.get("hba1c")
        self.left_sensory_score = kwargs.get("left_sensory_score")
        self.right_sensory_score = kwargs.get("right_sensory_score")