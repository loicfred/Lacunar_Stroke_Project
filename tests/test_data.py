import pandas as pd
import numpy as np
import src.data_simulation.patient_generator as patient_gen
import os

def flatten_patient_data(patient):
    """
    Convert a Patient object to a flat dictionary for CSV export.
    """
    patient_dict = patient.__dict__.copy()

    # Remove the reading_sequence (it's a list of objects)
    if 'reading_sequence' in patient_dict:
        del patient_dict['reading_sequence']

    # Extract pattern features if they exist as attributes
    pattern_features = {}
    for key in list(patient_dict.keys()):
        if key.startswith('pattern_'):
            pattern_features[key] = patient_dict[key]
            del patient_dict[key]

    # Add pattern features as separate columns
    for key, value in pattern_features.items():
        patient_dict[key] = value

    # Ensure all required fields exist
    required_fields = ['volatility_index', 'asymmetry_index', 'score_velocity']
    for field in required_fields:
        if field not in patient_dict:
            # Calculate missing fields
            if field == 'asymmetry_index' and 'left_sensory_score' in patient_dict and 'right_sensory_score' in patient_dict:
                left = patient_dict['left_sensory_score']
                right = patient_dict['right_sensory_score']
                avg = (left + right) / 2
                patient_dict[field] = abs(left - right) / (avg + 1) if avg > 0 else 0

    return patient_dict

def generate_and_save_training_data(num_patients=5000, csv_path="data/stroke_training_data.csv"):
    """
    Generate training data and save to CSV.
    """
    print(f"🔄 Generating {num_patients} complete patient profiles...")

    # Generate patients with pattern features
    patients = patient_gen.generate_batch_patients_data(
        num_patients,
        use_timeline=True,
        include_pattern_features=True
    )

    # Flatten the data
    flat_data = []
    for patient in patients:
        flat_data.append(flatten_patient_data(patient))

    # Create DataFrame
    df = pd.DataFrame(flat_data)

    # Ensure all pattern features columns exist (even if empty)
    pattern_cols = ['pattern_volatility_index', 'pattern_velocity_trend',
                    'pattern_stuttering_score', 'pattern_pattern_amplitude',
                    'pattern_asymmetry_progression', 'pattern_consistency_score']

    for col in pattern_cols:
        if col not in df.columns:
            df[col] = 0.0

    # Save to CSV
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df.to_csv(csv_path, index=False)

    print(f"\n==================================================")
    print(f"✅ SUCCESS: DATA MERGED AND EXPORTED")
    print(f"==================================================")
    print(f"📍 CSV Path: {csv_path}")
    print(f"📊 Total Records: {len(df)}")
    print(f"🔢 Columns: {len(df.columns)}")

    # Show a preview
    print(f"\nPreview of first 5 records:")
    print(df.head().to_string())

    # Check for important columns
    print(f"\n🔍 Checking critical columns:")
    critical_cols = ['volatility_index', 'asymmetry_index', 'score_velocity', 'impact_tier']
    for col in critical_cols:
        if col in df.columns:
            print(f"  - {col}: {df[col].notna().sum()} non-null values, range: {df[col].min():.3f} to {df[col].max():.3f}")
        else:
            print(f"  - {col}: MISSING!")

    # Check pattern features
    print(f"\n🎯 Pattern Features Summary:")
    pattern_cols_present = [col for col in df.columns if col.startswith('pattern_')]
    if pattern_cols_present:
        for col in pattern_cols_present[:5]:  # Show first 5
            print(f"  - {col}: mean={df[col].mean():.3f}, std={df[col].std():.3f}")
    else:
        print("  No pattern features found!")

    return df

if __name__ == "__main__":
    # Generate a smaller dataset for testing
    df = generate_and_save_training_data(
        num_patients=100,  # Start with 100 for testing
        csv_path="data/stroke_training_data.csv"
    )