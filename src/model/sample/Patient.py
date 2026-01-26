from model.sample.PatientDetails import PatientDetails
from model.sample.SensoryDetails import SensoryDetails

class Patient(PatientDetails, SensoryDetails):
    def __init__(self, patient_id, age_group, sex, systolic_bp, hba1c, smoking_history,
                 left_sensory_score, right_sensory_score, affected_side, asymmetry_label,
                 response_strength, impact_tier, score_velocity):
        # ✅ PatientDetails gets CONTINUOUS markers
        PatientDetails.__init__(
            self,
            patient_id=patient_id,
            age_group=age_group,
            sex=sex,
            smoking_history=smoking_history
        )

        # ✅ SensoryDetails gets ONLY sensory measurements
        SensoryDetails.__init__(
            self,
            left_sensory_score=left_sensory_score,
            right_sensory_score=right_sensory_score,
            systolic_bp=systolic_bp,  # Continuous (NOT hypertension binary)
            hba1c=hba1c,              # Continuous (NOT diabetes binary)
            affected_side=affected_side,
            asymmetry_label=asymmetry_label,
            impact_tier=impact_tier,
            score_velocity=score_velocity
        )

        self.response_strength = response_strength

    @staticmethod
    def create(p_details, s_details):
        # ✅ Extract CONTINUOUS values from PatientDetails
        return Patient(
            p_details.patient_id,
            p_details.age_group,
            p_details.sex,
            p_details.systolic_bp,    # Continuous
            p_details.hba1c,          # Continuous
            p_details.smoking_history,
            s_details.left_sensory_score,
            s_details.right_sensory_score,
            s_details.affected_side,
            s_details.asymmetry_label,
            s_details.response_strength,
            s_details.impact_tier,
            getattr(s_details, 'score_velocity', 0.0)
        )