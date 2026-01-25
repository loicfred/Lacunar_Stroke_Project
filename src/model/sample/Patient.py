from model.sample.PatientDetails import PatientDetails
from model.sample.SensoryDetails import SensoryDetails

class Patient(PatientDetails, SensoryDetails):
    def __init__(self, patient_id, age_group, sex, diabetes, smoking_history, left_sensory_score, right_sensory_score, affected_side, asymmetry_label, blood_pressure, response_strength, impact_tier, score_velocity):
        PatientDetails.__init__(self, patient_id, age_group, sex, diabetes, smoking_history)
        SensoryDetails.__init__(self, left_sensory_score, right_sensory_score, blood_pressure, affected_side, asymmetry_label, impact_tier, score_velocity)
        self.response_strength = response_strength

    @staticmethod
    def create(p_details, s_details):
        return Patient(p_details.patient_id, p_details.age_group, p_details.sex, p_details.diabetes, p_details.smoking_history,
                       s_details.left_sensory_score, s_details.right_sensory_score, s_details.affected_side, s_details.asymmetry_label, s_details.blood_pressure, s_details.response_strength, s_details.impact_tier,
                       getattr(s_details, 'score_velocity', 0.0))
