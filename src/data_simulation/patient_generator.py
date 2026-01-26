import random
import numpy as np
from model.sample.Patient import Patient
from model.sample.PatientDetails import PatientDetails
from model.sample.SensoryDetails import SensoryDetails

AGE_GROUPS = ["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]
SEXES = ["Male", "Female"]

def add_measurement_noise(score):
    """Adds Gaussian noise to simulate sensor/user variability (Ref 2)."""
    noise = random.normalvariate(0, 0.3)
    return round(max(0, min(10, score + noise)), 2)

def generate_vitals(has_hypertension):
    """Replaces binary (0/1) with Systolic BP (Ref 5)."""
    if has_hypertension:
        # Uncontrolled hypertension range
        systolic_bp = int(random.gauss(165, 15))
    else:
        # Healthy/Pre-hypertensive range
        systolic_bp = int(random.gauss(122, 10))
    return max(90, min(220, systolic_bp))

def generate_metabolic_data(has_diabetes):
    """Replaces binary (0/1) with HbA1c (Ref 6)."""
    if has_diabetes:
        # Diabetic range (random.gauss() for biological data)
        hba1c = random.gauss(7.8, 1.2)
    else:
        # Normal range
        hba1c = random.gauss(5.2, 0.3)
    return round(max(4.0, min(14.0, hba1c)), 1)



def generate_stuttering_pattern(base_score, impact_tier, num_readings=5):
    """
    Generates a stuttering pattern (up-down-up-down) characteristic of lacunar strokes.
    Returns a list of scores showing the cyclical pattern.
    """
    scores = []

    if impact_tier <= 1:  # Normal or mild cases - minimal stuttering
        # Small random fluctuations
        for i in range(num_readings):
            fluctuation = random.gauss(0, 0.15)
            scores.append(max(0, min(10, base_score + fluctuation)))

    elif impact_tier == 2:  # Moderate cases - mild stuttering
        # Mild up-down pattern: Down, up, down, up, down
        base_pattern = [-0.4, 0.3, -0.5, 0.4, -0.6]
        for i, change in enumerate(base_pattern):
            # Add some randomness to the pattern
            random_variation = random.gauss(0, 0.15)
            scores.append(max(0, min(10, base_score + change + random_variation)))

    else:  # Severe/Critical cases (tier 3-4) - strong stuttering
        # Pronounced up-down-up-down pattern with overall decline
        if impact_tier == 3:
            base_pattern = [-0.8, 0.5, -1.0, 0.6, -1.2]  # Significant fluctuations
        else:  # tier 4
            base_pattern = [-1.2, 0.8, -1.5, 1.0, -2.0]  # Major fluctuations

        for i, change in enumerate(base_pattern):
            # Each cycle gets progressively worse overall
            trend = -0.15 * i  # Small downward trend
            random_variation = random.gauss(0, 0.25)
            scores.append(max(0, min(10, base_score + change + trend + random_variation)))

    return scores



def generate_single_patient_details(patient_id: int) -> PatientDetails:
    # Logic for underlying condition probability
    has_htn = random.random() < 0.3
    has_db = random.random() < 0.2

    return PatientDetails(patient_id,
                          random.choice(AGE_GROUPS),
                          random.choice(SEXES),
                          #generate_vitals(has_htn),
                          #generate_metabolic_data(has_db),
                          random.choice([0, 1]))

#def generate_batch_patient_details(quantity: int) -> list:
    #if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")
    #patient_list = []
    #for i in range(1, quantity + 1):
        #patient_list.append(generate_single_patient_details(i))
    #return patient_list

def generate_single_sensory_details(patient_info=None):
    # Get risk-weighted probabilities
    risk_weight = 0
    if patient_info:
        if patient_info.systolic_bp > 140: risk_weight += 0.15
        if patient_info.hba1c > 6.5: risk_weight += 0.15
        if patient_info.smoking_history: risk_weight += 0.1

    # Create overlapping probabilities instead of hard thresholds
    prob_unilateral = 0.25 + (risk_weight * 0.2)  # Base 25%, up to 45% with risk
    prob_bilateral = 0.15 + (risk_weight * 0.1)   # Base 15%, up to 25% with risk
    prob_normal = 0.6 - (risk_weight * 0.3)       # Base 60%, down to 30% with risk

    # Normalize to ensure they sum to 1
    total = prob_unilateral + prob_bilateral + prob_normal
    prob_unilateral /= total
    prob_bilateral /= total
    prob_normal /= total

    # Generate systolic_bp and hba1c for THIS reading
    if patient_info:
        # Use patient's baseline but add realistic variation
        systolic_bp = max(90, min(220,
                                  patient_info.systolic_bp + random.gauss(0, 5)))
        hba1c = max(4.0, min(14.0,
                             patient_info.hba1c + random.gauss(0, 0.2)))
    else:
        # Generate random values if no patient_info provided
        is_hypertensive = random.random() < 0.3
        is_diabetic = random.random() < 0.2
        systolic_bp = int(random.gauss(165, 15)) if is_hypertensive else int(random.gauss(122, 10))
        hba1c = round(random.gauss(7.8, 1.2), 1) if is_diabetic else round(random.gauss(5.2, 0.3), 1)

    roll = random.random()

    # --- BILATERAL DEFICIT / NEUROPATHY ---
    if roll < prob_bilateral:
        # Generate base score with overlap to stroke cases
        base_score = random.gauss(6.0, 1.2)

        # Generate stuttering pattern for bilateral neuropathy
        # Neuropathy typically shows less dramatic stuttering than acute stroke
        stuttering_severity = random.choices([1, 2], weights=[0.7, 0.3])[0]
        left_scores = generate_stuttering_pattern(base_score, stuttering_severity)
        right_scores = generate_stuttering_pattern(base_score, stuttering_severity)

        # Take the last score as current measurement
        left_sensory = left_scores[-1]
        right_sensory = right_scores[-1]

        affected_side, response_strength, label = "Both", "Weak Global Response", 2
        tier = 4  # Bilateral is always tier 4 (critical)

    # --- UNILATERAL DEFICIT (Stroke) ---
    elif roll < prob_bilateral + prob_unilateral:
        # Generate base scores with overlapping distributions
        affected_base = random.gauss(6.0, 1.5)  # Overlaps with bilateral mean
        healthy_base = random.gauss(8.5, 1.0)   # Overlaps with normal mean

        # Determine stroke severity (tier 1-3)
        # More severe strokes are less common
        tier = random.choices([1, 2, 3], weights=[0.4, 0.4, 0.2])[0]

        # Generate stuttering pattern for affected side based on severity
        affected_scores = generate_stuttering_pattern(affected_base, tier)

        # Healthy side has minimal stuttering (tier 0-1)
        healthy_stuttering = 0 if random.random() < 0.7 else 1
        healthy_scores = generate_stuttering_pattern(healthy_base, healthy_stuttering)

        affected_score = affected_scores[-1]
        healthy_score = healthy_scores[-1]

        # Ensure affected side is actually worse (with some randomness)
        if affected_score > healthy_score - 0.5:
            # Make the difference more pronounced
            adjustment = random.gauss(-0.8, 0.3)
            affected_score = max(0, affected_score + adjustment)

        # Determine response strength based on difference
        diff = abs(healthy_score - affected_score)
        if diff < 2.5:
            response_strength = "Slightly Reduced"
            tier = max(tier, 1)  # Ensure at least tier 1
        elif diff < 4.0:
            response_strength = "Moderately Reduced"
            tier = max(tier, 2)  # Ensure at least tier 2
        else:
            response_strength = "Significantly Reduced"
            tier = max(tier, 3)  # Ensure at least tier 3

        # Randomly assign to left or right side
        if random.choice(["left", "right"]) == "left":
            left_sensory, right_sensory = affected_score, healthy_score
            affected_side = "Left"
        else:
            left_sensory, right_sensory = healthy_score, affected_score
            affected_side = "Right"

        label = 1

    # --- NORMAL ---
    else:
        # Base score with overlap to healthy side of stroke patients
        base = random.gauss(8.5, 0.8)

        # Normal patients have minimal stuttering
        left_scores = generate_stuttering_pattern(base, 0)
        right_scores = generate_stuttering_pattern(base, 0)

        left_sensory = left_scores[-1]
        right_sensory = right_scores[-1]

        affected_side, response_strength, label, tier = "None", "Strong Response", 0, 0

    # Apply measurement noise (additional to stuttering pattern)
    left_sensory = add_measurement_noise(left_sensory)
    right_sensory = add_measurement_noise(right_sensory)

    # Create SensoryDetails with ALL required fields
    details = SensoryDetails(
        left_sensory_score=left_sensory,
        right_sensory_score=right_sensory,
        systolic_bp=systolic_bp,
        hba1c=hba1c,
        affected_side=affected_side,
        asymmetry_label=label,
        impact_tier=tier
    )
    details.response_strength = response_strength

    # Store the stuttering pattern for velocity calculation
    if 'affected_scores' in locals() and 'healthy_scores' in locals():
        details.stuttering_pattern = {
            'affected_side': affected_scores if 'affected_scores' in locals() else [],
            'healthy_side': healthy_scores if 'healthy_scores' in locals() else []
        }

    return details

def generate_sensory_with_velocity(patient_info=None):
    current_sensory = generate_single_sensory_details(patient_info)

    # Calculate velocity from stuttering pattern if available
    if hasattr(current_sensory, 'stuttering_pattern') and current_sensory.stuttering_pattern:
        # Use the actual pattern to calculate velocity
        pattern = current_sensory.stuttering_pattern

        if pattern['affected_side']:
            # Calculate velocity from affected side pattern
            affected_changes = [pattern['affected_side'][i+1] - pattern['affected_side'][i]
                                for i in range(len(pattern['affected_side'])-1)]
            if affected_changes:
                avg_affected_change = sum(affected_changes) / len(affected_changes)
                # Convert to points per hour (assuming 24h between readings)
                velocity = avg_affected_change / 24
            else:
                velocity = 0
        else:
            # For normal or bilateral cases
            velocity_options_hourly = {
                0: random.uniform(-0.005/24, 0.005/24),
                4: random.uniform(-0.04/24, -0.02/24)  # Bilateral decline
            }
            velocity = velocity_options_hourly.get(current_sensory.impact_tier, 0)
    else:
        # Fallback for cases without pattern
        velocity_options_hourly = {
            0: random.uniform(-0.005/24, 0.005/24),
            1: random.uniform(-0.01/24, 0.005/24),
            2: random.uniform(-0.02/24, 0),
            3: random.uniform(-0.03/24, -0.01/24),
            4: random.uniform(-0.04/24, -0.02/24)
        }
        velocity = velocity_options_hourly.get(current_sensory.impact_tier, 0)

    current_sensory.score_velocity = round(velocity, 6)

    # Calculate volatility from stuttering pattern
    if hasattr(current_sensory, 'stuttering_pattern') and current_sensory.stuttering_pattern:
        # Combine both sides for volatility calculation
        all_scores = []
        if current_sensory.stuttering_pattern.get('affected_side'):
            all_scores.extend(current_sensory.stuttering_pattern['affected_side'])
        if current_sensory.stuttering_pattern.get('healthy_side'):
            all_scores.extend(current_sensory.stuttering_pattern['healthy_side'])

        if all_scores:
            current_sensory.volatility_index = round(float(np.std(all_scores)), 3)
        else:
            current_sensory.volatility_index = round(random.uniform(0.1, 0.8), 3)
    else:
        # Fallback volatility
        if current_sensory.impact_tier > 1:
            current_sensory.volatility_index = round(random.uniform(0.5, 2.0), 3)
        else:
            current_sensory.volatility_index = round(random.uniform(0.1, 0.8), 3)

    return current_sensory

def generate_batch_patients_data(quantity: int = 5000) -> list:
    if quantity > 5000: raise ValueError("Maximum allowed simulated patients is 5000")
    patient_list = []
    for i in range(1, quantity + 1):
        patient_info = generate_single_patient_details(i)
        sensory = generate_sensory_with_velocity(patient_info)
        patient_list.append(Patient.create(patient_info, sensory))
    return patient_list