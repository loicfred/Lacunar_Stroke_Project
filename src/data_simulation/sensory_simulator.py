# sensory_simulator.py
# -----------------------------------
# This module simulates bilateral sensory perception data
# and generates asymmetry patterns relevant to early stroke detection.
# -----------------------------------

import random  # Used for stochastic sensory variation


def generate_sensory_profile(
    patient_id: int,
    asymmetric_probability: float = 0.5
) -> dict:
    """
    Generates bilateral sensory data for a single patient.

    Sensory values are scaled between 0 and 10, where:
    - Higher values indicate better sensory perception
    - Lower values indicate sensory impairment

    Parameters:
        patient_id (int): ID linking sensory data to patient profile
        asymmetric_probability (float): Probability of asymmetry

    Returns:
        dict: Simulated bilateral sensory measurements
    """

    # Baseline sensory sensitivity (normal range)
    base_sensation = random.uniform(7.0, 10.0)

    # Determine whether the patient exhibits asymmetry
    is_asymmetric = random.random() < asymmetric_probability

    if is_asymmetric:
        # Generate a mild-to-moderate unilateral sensory deficit
        deficit = random.uniform(1.0, 5.0)

        # Determine Severity
        if deficit < 2.5:
            severity = "Mild"
        elif deficit < 4.0:
            severity = "Moderate"
        else:
            severity = "Severe"

        # Randomly choose which side is affected
        if random.choice(["left", "right"]) == "left":
            left_sensory = max(0.0, base_sensation - deficit)
            right_sensory = base_sensation
            affected_side = "Left"
        else:
            right_sensory = max(0.0, base_sensation - deficit)
            left_sensory = base_sensation
            affected_side = "Right"

        # Label indicates presence of asymmetry
        label = 1

    else:
        # Independent variation for each side in normal patients
        left_sensory = base_sensation + random.uniform(-0.3, 0.3)
        right_sensory = base_sensation + random.uniform(-0.3, 0.3)
        affected_side = "None"
        severity = "None"
        label = 0

    diff = abs(left_sensory - right_sensory)
    avg = (left_sensory + right_sensory) / 2
    asymmetry_index = diff / avg if avg > 0 else 0.0

    return {
        # Link sensory data to patient profile
        "patient_id": patient_id,

        # Bilateral sensory perception scores
        "left_sensory_score": round(left_sensory, 2),
        "right_sensory_score": round(right_sensory, 2),

        "asymmetry_index": round(asymmetry_index, 4), # Normalized feature

        # Indicates which side is affected, if any
        "affected_side": affected_side,

        "severity": severity,

        # Classification label used for AI training
        # 1 = asymmetric, 0 = normal
        "asymmetry_label": label
    }


def generate_sensory_data(
    patients: list,
    asymmetric_probability: float = 0.5
) -> list:
    """
    Generates sensory profiles for all simulated patients.

    Parameters:
        patients (list): List of patient profiles
        asymmetric_probability (float): Probability of asymmetry

    Returns:
        list: List of sensory data dictionaries
    """

    sensory_data = []

    # Generate sensory data for each patient
    for patient in patients:
        sensory_data.append(
            generate_sensory_profile(
                patient["patient_id"],
                asymmetric_probability
            )
        )

    return sensory_data

