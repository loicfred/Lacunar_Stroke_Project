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
    # Generate conditions
    has_htn = random.random() < 0.3
    has_db = random.random() < 0.2

    # Generate BP values
    systolic, diastolic = generate_bp_values(has_htn)

    # Determine BP category based on values
    bp_category = determine_bp_category(systolic, diastolic)

    # Determine diabetes type if diabetic
    diabetes_type = "None"
    if has_db:
        diabetes_type = random.choices(["Type 1", "Type 2", "Gestational"],
                                       weights=[0.1, 0.85, 0.05])[0]

    # Generate blood glucose (correlated with HbA1c)
    hba1c_value = generate_metabolic_data(has_db)
    blood_glucose = generate_blood_glucose(hba1c_value, has_db)

    # Determine if on BP medication (higher chance if hypertensive)
    on_bp_medication = has_htn and random.random() < 0.6

    return PatientDetails(
        patient_id=patient_id,
        age_group=random.choice(AGE_GROUPS),
        sex=random.choice(SEXES),
        systolic_bp=systolic,
        diastolic_bp=diastolic,
        hba1c=hba1c_value,
        blood_glucose=blood_glucose,
        diabetes_type=diabetes_type,
        bp_category=bp_category,
        on_bp_medication=on_bp_medication,
        smoking_history=random.choice([0, 1])
    )

def generate_bp_values(has_hypertension):
    """Generate both systolic and diastolic BP"""
    if has_hypertension:
        systolic = int(random.gauss(145, 15))
        diastolic = int(random.gauss(95, 10))
    else:
        systolic = int(random.gauss(118, 8))
        diastolic = int(random.gauss(78, 5))

    return max(90, min(220, systolic)), max(60, min(130, diastolic))

def determine_bp_category(systolic, diastolic):
    """Determine BP category based on JNC 8 guidelines"""
    if systolic < 120 and diastolic < 80:
        return "Normal"
    elif systolic < 130 and diastolic < 80:
        return "Elevated"
    elif systolic < 140 or diastolic < 90:
        return "Hypertension Stage 1"
    else:
        return "Hypertension Stage 2"

def generate_blood_glucose(hba1c, has_diabetes):
    """Generate random blood glucose correlated with HbA1c"""
    if has_diabetes:
        base = random.gauss(180, 40)  # Higher for diabetics
    else:
        # Convert HbA1c to estimated average glucose
        base = (28.7 * hba1c) - 46.7

    return round(max(70, min(500, base)), 0)

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

    # ENHANCED VOLATILITY CALCULATION FOR LACUNAR STROKE PATTERNS
    if hasattr(current_sensory, 'stuttering_pattern') and current_sensory.stuttering_pattern:
        # Combine both sides for volatility calculation
        all_scores = []
        if current_sensory.stuttering_pattern.get('affected_side'):
            all_scores.extend(current_sensory.stuttering_pattern['affected_side'])
        if current_sensory.stuttering_pattern.get('healthy_side'):
            all_scores.extend(current_sensory.stuttering_pattern['healthy_side'])

        if all_scores:
            # Calculate base volatility
            base_volatility = float(np.std(all_scores))

            # ENHANCE VOLATILITY FOR LACUNAR STROKE PATTERNS
            # Lacunar infarcts (tiers 2-3) should show pronounced stuttering
            if current_sensory.impact_tier in [2, 3]:  # Moderate to severe unilateral
                # Add additional noise to simulate lacunar stuttering
                noisy_scores = [score + random.gauss(0, 0.4) for score in all_scores]
                base_volatility = float(np.std(noisy_scores))

                # Ensure minimum volatility for lacunar patterns
                if current_sensory.impact_tier == 2:  # Moderate
                    base_volatility = max(1.5, base_volatility)
                else:  # Severe (tier 3)
                    base_volatility = max(2.0, base_volatility)

            # Cap volatility at reasonable maximum
            base_volatility = min(base_volatility, 3.5)

            current_sensory.volatility_index = round(base_volatility, 3)
        else:
            # Fallback with clinical ranges for lacunar strokes
            clinical_volatility_ranges = {
                0: (0.1, 0.5),    # Normal: minimal fluctuation
                1: (0.5, 1.2),    # Mild unilateral: some variability
                2: (1.5, 2.5),    # Moderate unilateral: LACUNAR PATTERN RANGE
                3: (2.0, 3.5),    # Severe unilateral: PRONOUNCED LACUNAR
                4: (0.5, 1.5)     # Bilateral: more consistent deficit
            }
            min_v, max_v = clinical_volatility_ranges.get(current_sensory.impact_tier, (0.1, 1.0))
            current_sensory.volatility_index = round(random.uniform(min_v, max_v), 3)
    else:
        # Clinical volatility ranges based on impact tier
        clinical_volatility_ranges = {
            0: (0.1, 0.5),    # Normal
            1: (0.5, 1.2),    # Mild unilateral risk
            2: (1.5, 2.5),    # Moderate unilateral - LACUNAR INFARCT
            3: (2.0, 3.5),    # Severe unilateral - PRONOUNCED LACUNAR
            4: (0.5, 1.5)     # Bilateral neuropathy
        }

        min_v, max_v = clinical_volatility_ranges.get(current_sensory.impact_tier, (0.1, 1.0))
        current_sensory.volatility_index = round(random.uniform(min_v, max_v), 3)

    # ADDITIONAL VALIDATION: Ensure volatility aligns with clinical presentation
    if current_sensory.impact_tier in [2, 3] and current_sensory.volatility_index < 1.2:
        # Lacunar strokes should not have low volatility - adjust upward
        current_sensory.volatility_index = round(random.uniform(1.5, 2.8), 3)

    return current_sensory


def generate_patient_timeline(patient_id, num_readings=5):
    """Generate multiple readings for the same patient over time"""
    patient_info = generate_single_patient_details(patient_id)
    timeline = []

    for i in range(num_readings):
        # Each reading should show progression/regression
        sensory = generate_single_sensory_details(patient_info)

        # Add temporal component (worsening/improving over time)
        if i > 0:
            # Adjust based on stroke progression
            if sensory.impact_tier > 0:
                # Lacunar strokes fluctuate
                fluctuation = random.gauss(0, 0.3)
                sensory.left_sensory_score = max(0, sensory.left_sensory_score + fluctuation)
                sensory.right_sensory_score = max(0, sensory.right_sensory_score + fluctuation)

        timeline.append(sensory)

    # Calculate REAL volatility from the timeline
    left_scores = [s.left_sensory_score for s in timeline]
    right_scores = [s.right_sensory_score for s in timeline]
    all_scores = left_scores + right_scores

    real_volatility = np.std(all_scores) if len(all_scores) > 1 else 0

    # For the "current" patient record, use the last reading with calculated volatility
    current_sensory = timeline[-1]

    # Update the sensory object with calculated values
    current_sensory.volatility_index = round(real_volatility, 3)

    # Calculate velocity (change over time)
    if len(timeline) >= 2:
        time_hours = 24 * (len(timeline) - 1)  # Assuming 24h between readings
        score_change = current_sensory.left_sensory_score - timeline[0].left_sensory_score
        current_sensory.score_velocity = round(score_change / time_hours, 6)
    else:
        current_sensory.score_velocity = 0

    # Calculate asymmetry index (this should already be in SensoryDetails)
    if hasattr(current_sensory, 'left_sensory_score') and hasattr(current_sensory, 'right_sensory_score'):
        if current_sensory.left_sensory_score + current_sensory.right_sensory_score > 0:
            asymmetry = abs(current_sensory.left_sensory_score - current_sensory.right_sensory_score) / \
                        (current_sensory.left_sensory_score + current_sensory.right_sensory_score)
            current_sensory.asymmetry_index = round(asymmetry, 3)

    return Patient.create(patient_info, current_sensory)


def generate_batch_patients_data(quantity: int = 5000, use_timeline: bool = True) -> list:
    """
    Generate batch patient data.

    Args:
        quantity: Number of patients to generate
        use_timeline: If True, generates realistic patient timelines with
                     calculated volatility from multiple readings.
                     If False, uses the old method with simulated volatility.
    """
    if quantity > 5000:
        raise ValueError("Maximum allowed simulated patients is 5000")

    patient_list = []

    for i in range(1, quantity + 1):
        if use_timeline:
            # Use the improved timeline method (RECOMMENDED)
            patient = generate_patient_timeline(i, num_readings=5)
        else:
            # Old method (for comparison only)
            patient_info = generate_single_patient_details(i)
            sensory = generate_sensory_with_velocity(patient_info)
            patient = Patient.create(patient_info, sensory)

        patient_list.append(patient)

    return patient_list