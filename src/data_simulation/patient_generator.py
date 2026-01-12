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
    if quantity > 1000: raise ValueError("Maximum allowed simulated patients is 1000")
    patient_list = []
    for i in range(1, quantity + 1):
        patient_list.append(generate_single_patient_details(i))
    return patient_list


# This creates a single sensory details object
def generate_single_sensory_details(asymmetric_probability: float = 0.4, bilateral_probability: float = 0.1) -> SensoryDetails:
    base_sensation = random.uniform(7.0, 10.0) # 7-10 means healthy
    roll = random.random()
    # --- CASE 1: BILATERAL DEFICIT (Both sides low) ---
    if roll < bilateral_probability:
        # Significant drop on both sides
        left_sensory = random.uniform(1.0, 4.5)
        right_sensory = random.uniform(1.0, 4.5)
        affected_side = "Both"
        severity = "Severe (Bilateral)"
        label = 2

    # --- CASE 2: UNILATERAL DEFICIT (One side low) ---
    elif roll < (bilateral_probability + asymmetric_probability):
        deficit = random.uniform(1.5, 5.0)

        if deficit < 2.5: severity = "Mild"
        elif deficit < 4.0: severity = "Moderate"
        else: severity = "Severe"

        if random.choice(["left", "right"]) == "left":
            left_sensory = max(0.0, base_sensation - deficit)
            right_sensory = base_sensation
            affected_side = "Left"
        else:
            right_sensory = max(0.0, base_sensation - deficit)
            left_sensory = base_sensation
            affected_side = "Right"
        label = 1

    # --- CASE 3: NORMAL (Both sides high) ---
    else:
        left_sensory = base_sensation + random.uniform(-0.3, 0.3)
        right_sensory = base_sensation + random.uniform(-0.3, 0.3)
        affected_side = "None"
        severity = "None"
        label = 0

    details = SensoryDetails(left_sensory, right_sensory, affected_side, label)
    details.severity = severity
    return details


# This creates X number of patients with their details and sensory details.
def generate_batch_patients_data(quantity: int = 1000) -> list:
    if quantity > 1000: raise ValueError("Maximum allowed simulated patients is 1000")

    patient_list = []
    for i in range(1, quantity + 1):
        patient = generate_single_patient_details(i)
        sensory = generate_single_sensory_details()

        patient_list.append(Patient.create(patient, sensory))

    return patient_list



