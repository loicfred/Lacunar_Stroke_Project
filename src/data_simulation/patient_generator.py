import random
import numpy as np
import math
from datetime import datetime

# Simple Patient class to hold data
class SimplePatient:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

def generate_patient_data(quantity=5000):
    """Generate patient data with proper volatility and pattern features."""
    patients = []

    print(f"📊 Generating {quantity} patients with pattern features...")

    for i in range(1, quantity + 1):
        # Generate basic patient info
        patient_data = {
            'patient_id': i,
            'age_group': random.choice(["30-39", "40-49", "50-59", "60-69", "70-79", "80+"]),
            'sex': random.choice(["Male", "Female"]),
            'systolic_bp': random.randint(100, 180),
            'diastolic_bp': random.randint(60, 110),
            'hba1c': round(random.uniform(4.0, 10.0), 1),
            'blood_glucose': random.randint(80, 200),
            'diabetes_type': random.choices(["None", "Type 1", "Type 2"], weights=[0.8, 0.05, 0.15])[0],
            'bp_category': random.choice(["Normal", "Elevated", "Hypertension Stage 1", "Hypertension Stage 2"]),
            'on_bp_medication': random.randint(0, 2),
            'smoking_history': random.randint(0, 1),
            'timestamp': datetime.now().isoformat()
        }

        # Determine impact tier
        tier_prob = random.random()
        if tier_prob < 0.57:  # 57% normal
            impact_tier = 0
            left_score = random.uniform(8.0, 10.0)
            right_score = random.uniform(8.0, 10.0)
            affected_side = "None"
            response_strength = "Strong Response"
            asymmetry_label = 0

        elif tier_prob < 0.685:  # 11.5% mild unilateral
            impact_tier = 1
            if random.choice([True, False]):
                left_score = random.uniform(6.0, 7.5)
                right_score = random.uniform(8.0, 9.5)
                affected_side = "Left"
            else:
                left_score = random.uniform(8.0, 9.5)
                right_score = random.uniform(6.0, 7.5)
                affected_side = "Right"
            response_strength = "Slightly Reduced"
            asymmetry_label = 1

        elif tier_prob < 0.793:  # 10.8% moderate unilateral
            impact_tier = 2
            if random.choice([True, False]):
                left_score = random.uniform(4.5, 6.5)
                right_score = random.uniform(8.0, 9.5)
                affected_side = "Left"
            else:
                left_score = random.uniform(8.0, 9.5)
                right_score = random.uniform(4.5, 6.5)
                affected_side = "Right"
            response_strength = "Moderately Reduced"
            asymmetry_label = 1

        elif tier_prob < 0.842:  # 4.9% severe unilateral
            impact_tier = 3
            if random.choice([True, False]):
                left_score = random.uniform(3.0, 5.0)
                right_score = random.uniform(8.0, 9.5)
                affected_side = "Left"
            else:
                left_score = random.uniform(8.0, 9.5)
                right_score = random.uniform(3.0, 5.0)
                affected_side = "Right"
            response_strength = "Significantly Reduced"
            asymmetry_label = 1

        else:  # 15.8% bilateral
            impact_tier = 4
            left_score = random.uniform(4.0, 6.5)
            right_score = random.uniform(4.0, 6.5)
            affected_side = "Both"
            response_strength = "Weak Global Response"
            asymmetry_label = 2

        # Add measurement noise
        left_score = round(max(0, min(10, left_score + random.gauss(0, 0.3))), 2)
        right_score = round(max(0, min(10, right_score + random.gauss(0, 0.3))), 2)

        # Calculate asymmetry index
        avg_score = (left_score + right_score) / 2
        if avg_score > 0:
            asymmetry_index = abs(left_score - right_score) / avg_score
        else:
            asymmetry_index = 0.0

        # Generate realistic volatility based on impact tier
        volatility_ranges = {
            0: (0.1, 0.5),    # Normal
            1: (0.5, 1.5),    # Mild
            2: (1.2, 2.5),    # Moderate (lacunar)
            3: (1.8, 3.0),    # Severe
            4: (0.5, 1.8)     # Bilateral
        }

        min_v, max_v = volatility_ranges.get(impact_tier, (0.1, 1.0))
        volatility = random.uniform(min_v, max_v)

        # Add extra variability for lacunar patterns
        if impact_tier in [2, 3]:
            volatility += random.uniform(0.3, 0.8)

        # Generate score velocity
        velocity_ranges = {
            0: (-0.001, 0.001),
            1: (-0.01, 0.005),
            2: (-0.02, 0.0),
            3: (-0.03, -0.01),
            4: (-0.02, -0.005)
        }

        min_vel, max_vel = velocity_ranges.get(impact_tier, (-0.01, 0.01))
        velocity = random.uniform(min_vel, max_vel)

        # Add pattern features
        if impact_tier == 0:  # Normal
            pattern_volatility = volatility
            pattern_stuttering_score = random.randint(0, 1)
            pattern_amplitude = random.uniform(0.1, 0.8)
            pattern_consistency = random.uniform(0.8, 1.0)
            pattern_type = "stable"

        elif impact_tier == 1:  # Mild
            pattern_volatility = volatility
            pattern_stuttering_score = random.randint(1, 2)
            pattern_amplitude = random.uniform(0.5, 1.5)
            pattern_consistency = random.uniform(0.6, 0.9)
            pattern_type = random.choice(["mild_stuttering", "stable"])

        elif impact_tier == 2:  # Moderate (lacunar)
            pattern_volatility = volatility
            pattern_stuttering_score = random.randint(2, 3)
            pattern_amplitude = random.uniform(1.0, 2.5)
            pattern_consistency = random.uniform(0.4, 0.7)
            pattern_type = random.choice(["moderate_stuttering", "high_stuttering"])

        elif impact_tier == 3:  # Severe
            pattern_volatility = volatility
            pattern_stuttering_score = random.randint(3, 4)
            pattern_amplitude = random.uniform(1.5, 3.0)
            pattern_consistency = random.uniform(0.3, 0.6)
            pattern_type = "high_stuttering"

        else:  # Bilateral
            pattern_volatility = volatility
            pattern_stuttering_score = random.randint(1, 2)
            pattern_amplitude = random.uniform(0.5, 1.8)
            pattern_consistency = random.uniform(0.7, 0.9)
            pattern_type = random.choice(["stable", "mild_stuttering"])

        # Add remaining data to patient_data
        patient_data.update({
            'left_sensory_score': left_score,
            'right_sensory_score': right_score,
            'affected_side': affected_side,
            'asymmetry_label': asymmetry_label,
            'impact_tier': impact_tier,
            'score_velocity': round(velocity, 6),
            'volatility_index': round(volatility, 3),
            'asymmetry_index': round(asymmetry_index, 3),
            'response_strength': response_strength,
            # Pattern features
            'pattern_volatility': round(pattern_volatility, 3),
            'pattern_velocity_trend': round(velocity * random.uniform(0.8, 1.2), 6),
            'pattern_stuttering_score': pattern_stuttering_score,
            'pattern_amplitude': round(pattern_amplitude, 3),
            'pattern_asymmetry_progression': round(random.uniform(-0.1, 0.1), 4),
            'pattern_type': pattern_type,
            'pattern_consistency': round(pattern_consistency, 3),
            'pattern_reading_count': 5
        })

        # Create patient object
        patient = SimplePatient(**patient_data)
        patients.append(patient)

        # Print first 5 for verification
        if i <= 5:
            print(f"✅ Patient {i}: tier={impact_tier}, "
                  f"volatility={volatility:.3f}, "
                  f"pattern={pattern_type}")

    # Statistics
    if patients:
        volatilities = [getattr(p, 'volatility_index', 0.0) for p in patients]

        print(f"\n📊 Generation Complete:")
        print(f"  • Total patients: {len(patients)}")
        print(f"  • Avg volatility: {np.mean(volatilities):.3f}")
        print(f"  • Min volatility: {min(volatilities):.3f}")
        print(f"  • Max volatility: {max(volatilities):.3f}")

        zero_count = sum(1 for v in volatilities if v == 0.0)
        if zero_count > 0:
            print(f"  ⚠️ Patients with zero volatility: {zero_count} ({(zero_count/len(volatilities))*100:.1f}%)")

    return patients

# Update the import in data_pipeline.py to use this function
# Replace: patients = patient_gen.generate_batch_patients_data(...)
# With: patients = patient_gen.generate_patient_data(amount)