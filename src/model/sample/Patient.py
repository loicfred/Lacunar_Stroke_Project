from model.sample.PatientDetails import PatientDetails
from model.sample.SensoryDetails import SensoryDetails

class Patient(PatientDetails, SensoryDetails):
    def __init__(self, patient_id, age_group, sex, systolic_bp, diastolic_bp,
                 hba1c, blood_glucose, diabetes_type, bp_category, on_bp_medication,
                 smoking_history, left_sensory_score, right_sensory_score,
                 affected_side, asymmetry_label, response_strength, impact_tier,
                 score_velocity):

        PatientDetails.__init__(
            self,
            patient_id=patient_id,
            age_group=age_group,
            sex=sex,
            systolic_bp=systolic_bp,
            diastolic_bp=diastolic_bp,  # NEW
            hba1c=hba1c,
            blood_glucose=blood_glucose,  # NEW
            diabetes_type=diabetes_type,  # NEW
            bp_category=bp_category,  # NEW
            on_bp_medication=on_bp_medication,  # NEW
            smoking_history=smoking_history
        )

        SensoryDetails.__init__(
            self,
            left_sensory_score=left_sensory_score,
            right_sensory_score=right_sensory_score,
            systolic_bp=systolic_bp,
            hba1c=hba1c,
            affected_side=affected_side,
            asymmetry_label=asymmetry_label,
            impact_tier=impact_tier,
            score_velocity=score_velocity
        )
        self.response_strength = response_strength

    @staticmethod
    def create(p_details, s_details):
        return Patient(
            patient_id=p_details.patient_id,
            age_group=p_details.age_group,
            sex=p_details.sex,
            systolic_bp=p_details.systolic_bp,
            diastolic_bp=getattr(p_details, 'diastolic_bp', 80),  # NEW with default
            hba1c=p_details.hba1c,
            blood_glucose=getattr(p_details, 'blood_glucose', 100),  # NEW with default
            diabetes_type=getattr(p_details, 'diabetes_type', 'None'),  # NEW with default
            bp_category=getattr(p_details, 'bp_category', 'Normal'),  # NEW with default
            on_bp_medication=getattr(p_details, 'on_bp_medication', 0),  # NEW with default
            smoking_history=p_details.smoking_history,
            left_sensory_score=s_details.left_sensory_score,
            right_sensory_score=s_details.right_sensory_score,
            affected_side=s_details.affected_side,
            asymmetry_label=s_details.asymmetry_label,
            response_strength=s_details.response_strength,
            impact_tier=s_details.impact_tier,
            score_velocity=getattr(s_details, 'score_velocity', 0.0)
        )