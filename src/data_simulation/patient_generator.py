# -----------------------------------
# This section is used to generate patient details.
# -----------------------------------

import random
from model.sample.Patient import Patient
from model.sample.PatientDetails import PatientDetails
from model.sample.SensoryDetails import SensoryDetails

AGE_GROUPS = ["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
SEXES = ["Male", "Female"]


# This creates a single patient details object
def generate_single_patient_details(patient_id: int) -> PatientDetails:
    return PatientDetails(patient_id,
                          random.choice(AGE_GROUPS),
                          random.choice(SEXES),
                          random.choice([0, 1]),
                          random.choice([0, 1]))


def generate_batch_patient_details(quantity: int) -> list:
    if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")
    patient_list = []
    for i in range(1, quantity + 1):
        patient_list.append(generate_single_patient_details(i))
    return patient_list


# This creates a single sensory details object
def generate_single_sensory_details(patient_info=None) -> SensoryDetails:
    roll = random.random()

    # IMPROVEMENT: Clinical Bias
    # If the patient has health risks, increase the chance of a deficit (Case 1 or 2)
    risk_weight = 0
    if patient_info:
        if patient_info.hypertension: risk_weight += 0.15
        if patient_info.diabetes: risk_weight += 0.15
        if patient_info.smoking_history: risk_weight += 0.1

    # Adjust roll based on risk (making deficits more likely)
    roll = max(0, roll - risk_weight)

    # --- CASE 1: BILATERAL DEFICIT ---
    if roll < 0.3:
        left_sensory = round(random.uniform(1.0, 6.5), 2)
        right_sensory = round(left_sensory + random.uniform(-0.2, 0.2), 2)
        affected_side, response_strength, label, tier = "Both", "Weak Global Response", 2, 4

    # --- CASE 2: UNILATERAL DEFICIT ---
    elif roll < 0.6:
        base_sensation = random.uniform(7.5, 10.0)
        deficit = random.uniform(2.0, 6.0)
        tier = 1 if deficit < 3.0 else (2 if deficit < 4.5 else 3)
        response_strength = ["Slightly Reduced", "Moderately Reduced", "Significantly Reduced"][tier-1]

        if random.choice(["left", "right"]) == "left":
            left_sensory, right_sensory = round(max(0, base_sensation - deficit), 2), round(base_sensation, 2)
            affected_side = "Left"
        else:
            left_sensory, right_sensory = round(base_sensation, 2), round(max(0, base_sensation - deficit), 2)
            affected_side = "Right"
        label = 1

    # --- CASE 3: NORMAL ---
    else:
        left_sensory = round(random.uniform(7.5, 10.0), 2)
        right_sensory = round(left_sensory + random.uniform(-0.3, 0.3), 2)
        affected_side, response_strength, label, tier = "None", "Strong Response", 0, 0

    blood_pressure = round(random.uniform(80, 150), 2)

    details = SensoryDetails(left_sensory, right_sensory, blood_pressure, affected_side, label)
    details.response_strength = response_strength
    details.impact_tier = tier
    return details


def generate_sensory_with_velocity(patient_info=None):
    """
    Generates current sensory data plus a calculated velocity
    based on a simulated previous reading.
    """
    # 1. Generate the 'Current' state using your existing logic
    current_sensory = generate_single_sensory_details(patient_info)

    # 2. Simulate a 'Previous' state (Baseline)
    # We assume the patient was mostly healthy 3 to 24 hours ago
    prev_left = random.uniform(8.5, 10.0)
    prev_right = random.uniform(8.5, 10.0)
    time_gap = random.choice([3, 6, 12, 24]) # Hours since last check

    # 3. Calculate Velocity (Change per hour)
    # Velocity = (Current - Previous) / Time
    left_vel = (current_sensory.left_sensory_score - prev_left) / time_gap
    right_vel = (current_sensory.right_sensory_score - prev_right) / time_gap

    # We take the 'worst' (most negative) velocity as our feature
    score_velocity = min(left_vel, right_vel)

    # Attach these to the object so the pipeline can see them
    current_sensory.score_velocity = round(score_velocity, 3)
    current_sensory.time_gap = time_gap

    return current_sensory

def generate_batch_patients_data(quantity: int = 5000) -> list:
    if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")

    patient_list = []
    for i in range(1, quantity + 1):
        patient_info = generate_single_patient_details(i)
        # IMPROVEMENT: Use the velocity-aware generator
        sensory = generate_sensory_with_velocity(patient_info)

        patient_list.append(Patient.create(patient_info, sensory))

    return patient_list



