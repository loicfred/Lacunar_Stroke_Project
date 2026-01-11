import random

def generate_sensory_profile(
        patient_id: int,
        asymmetric_probability: float = 0.4,
        bilateral_probability: float = 0.1
) -> dict:
    """
    Generates sensory data including Normal, Unilateral, and Bilateral deficits.
    
    Labels:
    0: Normal (High/Balanced)
    1: Unilateral (Lopsided/Asymmetric)
    2: Bilateral (Low/Balanced)
    """

    # 1. Base healthy range
    base_sensation = random.uniform(7.0, 10.0)

    # Determine state based on probabilities
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

    # 2. Calculate Asymmetry Index (AI)
    diff = abs(left_sensory - right_sensory)
    avg = (left_sensory + right_sensory) / 2
    asymmetry_index = diff / avg if avg > 0 else 0.0

    return {
        "patient_id": patient_id,
        "left_sensory_score": round(left_sensory, 2),
        "right_sensory_score": round(right_sensory, 2),
        "asymmetry_index": round(asymmetry_index, 4),
        "affected_side": affected_side,
        "severity": severity,
        "asymmetry_label": label  # Multi-class: 0, 1, or 2
    }

def generate_sensory_data(patients: list, asymmetric_probability: float = 0.4, bilateral_probability: float = 0.1) -> list:
    sensory_data = []
    for patient in patients:
        sensory_data.append(
            generate_sensory_profile(patient["patient_id"], asymmetric_probability, bilateral_probability)
        )
    return sensory_data