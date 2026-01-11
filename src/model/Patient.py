import json

from model.PatientDetails import PatientDetails
from model.SensoryDetails import SensoryDetails


class Patient(PatientDetails, SensoryDetails):
    def __init__(self, patient_id, age_group, sex, hypertension, diabetes, smoking_history, left_sensory_score, right_sensory_score, asymmetry_index, affected_side, severity, asymmetry_label):
        PatientDetails.__init__(self, patient_id, age_group, sex, hypertension, diabetes, smoking_history)
        SensoryDetails.__init__(self, left_sensory_score, right_sensory_score, asymmetry_index, affected_side, severity, asymmetry_label)

    @staticmethod
    def create(p_details, s_details):
        return Patient(p_details.patient_id, p_details.age_group, p_details.sex, p_details.hypertension, p_details.diabetes, p_details.smoking_history,
                       s_details.left_sensory_score, s_details.right_sensory_score, s_details.asymmetry_index, s_details.affected_side, s_details.severity, s_details.asymmetry_label)