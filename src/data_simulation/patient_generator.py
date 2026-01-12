# -----------------------------------
# This section is used to generate patient details.
# -----------------------------------

import random
from model.Patient import Patient
from model.PatientDetails import PatientDetails
from model.SensoryDetails import SensoryDetails

AGE_GROUPS = ["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
SEXES = ["Male", "Female"]


# This creates a single patient details object
def generate_single_patient_details(patient_id: int) -> PatientDetails:
    return PatientDetails(patient_id,
                          random.choice(AGE_GROUPS),
                          random.choice(SEXES),
                          random.choice([0, 1]),
                          random.choice([0, 1]),
                          random.choice([0, 1]))
def generate_batch_patient_details(quantity: int) -> list:
    if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")
    patient_list = []
    for i in range(1, quantity + 1):
        patient_list.append(generate_single_patient_details(i))
    return patient_list


# This creates a single sensory details object
def generate_single_sensory_details(asymmetric_probability: float = 0.3, bilateral_probability: float = 0.3) -> SensoryDetails:
    roll = random.random()
    # --- CASE 1: BILATERAL DEFICIT (Both sides low) ---
    if roll < bilateral_probability:
        # Significant drop on both sides
        left_sensory = round(random.uniform(1.0, 6.5), 2)
        right_sensory = round(left_sensory + random.uniform(-0.2, 0.2), 2)
        affected_side = "Both"
        response_strength = "Weak Global Response"
        label = 2
        tier = 4

    # --- CASE 2: UNILATERAL DEFICIT (One side low) ---
    elif roll < (bilateral_probability + asymmetric_probability):
        base_sensation = random.uniform(7.5, 10.0) # Healthy side
        deficit = random.uniform(2.0, 6.0)
        # Assign tiers based on the size of the gap
        tier = 1 if deficit < 3.0 else (2 if deficit < 4.5 else 3)
        response_strength = ["Slightly Reduced", "Moderately Reduced", "Significantly Reduced"][tier-1]

        if random.choice(["left", "right"]) == "left":
            left_sensory, right_sensory = round(max(0, base_sensation - deficit), 2), round(base_sensation, 2)
            affected_side = "Left"
        else:
            left_sensory, right_sensory = round(base_sensation, 2), round(max(0, base_sensation - deficit), 2)
            affected_side = "Right"
        label = 1

    # --- CASE 3: NORMAL (Both sides high) ---
    else:
        left_sensory = round(random.uniform(7.5, 10.0), 2)
        right_sensory = round(left_sensory + random.uniform(-0.3, 0.3), 2)
        affected_side = "None"
        response_strength = "Strong Response"
        label = 0
        tier = 0

    details = SensoryDetails(left_sensory, right_sensory, affected_side, label)
    details.response_strength = response_strength
    details.impact_tier = tier
    return details


# This creates X number of patients with their details and sensory details.
def generate_batch_patients_data(quantity: int = 5000) -> list:
    if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")

    patient_list = []
    for i in range(1, quantity + 1):
        patient = generate_single_patient_details(i)
        sensory = generate_single_sensory_details()

        patient_list.append(Patient.create(patient, sensory))

    return patient_list



