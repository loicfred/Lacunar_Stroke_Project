class Detailed_Report:
    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.email = kwargs.get("email")
        self.role = kwargs.get("role")

        self.patient_id = kwargs.get("patient_id")
        self.age_group = kwargs.get("age_group")
        self.sex = kwargs.get("sex")
        self.hypertension = kwargs.get("hypertension")
        self.diabetes = kwargs.get("diabetes")
        self.smoking_history = kwargs.get("smoking_history")
        self.first_name = kwargs.get("first_name")
        self.last_name = kwargs.get("last_name")

        self.timestamp = kwargs.get("timestamp")
        self.left_sensory_score = kwargs.get("left_sensory_score")
        self.right_sensory_score = kwargs.get("right_sensory_score")

        self.asymmetry_difference = kwargs.get("asymmetry_difference")
        self.average_asymmetry = kwargs.get("average_asymmetry")
        self.asymmetry_index = kwargs.get("asymmetry_index")
