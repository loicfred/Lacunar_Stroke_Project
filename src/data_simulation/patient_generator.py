# patient_generator.py
# -----------------------------------
# This module generates simulated patient profile data
# including demographics and clinical risk factors.
# -----------------------------------

import random  # Used for random selection of attributes

# Predefined age categories commonly used in stroke studies
AGE_GROUPS = [
    "40-49",
    "50-59",
    "60-69",
    "70-79"
]

# Biological sex categories
SEXES = ["Male", "Female"]


def generate_patient(patient_id: int) -> dict:
    """
    Generates a single simulated patient profile.

    Parameters:
        patient_id (int): Unique identifier for the patient

    Returns:
        dict: Patient demographic and clinical risk data
    """

    return {
        # Unique patient identifier
        "patient_id": patient_id,

        # Age group instead of exact age to reduce bias
        "age_group": random.choice(AGE_GROUPS),

        # Sex of the patient
        "sex": random.choice(SEXES),

        # Clinical risk factors represented as binary values
        # 1 = present, 0 = absent
        "hypertension": random.choice([0, 1]),
        "diabetes": random.choice([0, 1]),
        "smoking_history": random.choice([0, 1])
    }


def generate_patients(num_patients: int = 1000) -> list:
    """
    Generates a list of simulated patient profiles.

    Parameters:
        num_patients (int): Number of patients to simulate (max 1000)

    Returns:
        list: List of patient profile dictionaries
    """

    # Enforce upper limit to maintain dataset realism
    if num_patients > 1000:
        raise ValueError("Maximum allowed simulated patients is 1000")

    patients = []

    # Generate each patient profile
    for i in range(1, num_patients + 1):
        patients.append(generate_patient(i))

    return patients
