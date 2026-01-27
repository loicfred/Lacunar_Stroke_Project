# -----------------------------------
# This pipeline is used to generate a JSON and CSV of simulated patient data.
# -----------------------------------
import os
import pandas as pd
import numpy as np
from datetime import datetime
import data_simulation.patient_generator as patient_gen

def extract_all_attributes(obj):
    """Extract all attributes from an object, including nested objects."""
    attributes = {}

    # Get all attributes of the object
    for attr_name in dir(obj):
        # Skip private and special methods
        if attr_name.startswith('_'):
            continue

        try:
            attr_value = getattr(obj, attr_name)

            # Skip methods
            if callable(attr_value):
                continue

            # Handle nested objects
            if hasattr(attr_value, '__dict__'):
                # Recursively extract attributes from nested objects
                nested_attrs = extract_all_attributes(attr_value)
                for nested_key, nested_value in nested_attrs.items():
                    attributes[f"{attr_name}_{nested_key}"] = nested_value
            else:
                attributes[attr_name] = attr_value

        except:
            continue

    return attributes

def flatten_patient_data(patient):
    """Flatten a single patient into a dictionary format."""
    # First, try to extract all attributes directly from the patient
    patient_dict = extract_all_attributes(patient)

    # Ensure we have all required columns
    required_columns = [
        'patient_id', 'age_group', 'sex', 'systolic_bp', 'diastolic_bp',
        'hba1c', 'blood_glucose', 'diabetes_type', 'bp_category',
        'on_bp_medication', 'smoking_history', 'left_sensory_score',
        'right_sensory_score', 'affected_side', 'asymmetry_label',
        'impact_tier', 'score_velocity', 'volatility_index', 'timestamp',
        'asymmetry_index', 'response_strength'
    ]

    # Add pattern features
    pattern_features = [
        'pattern_volatility', 'pattern_velocity_trend', 'pattern_stuttering_score',
        'pattern_amplitude', 'pattern_asymmetry_progression', 'pattern_type',
        'pattern_consistency', 'pattern_reading_count'
    ]

    required_columns.extend(pattern_features)

    # Create final dictionary with all required columns
    final_dict = {}
    for col in required_columns:
        if col in patient_dict:
            final_dict[col] = patient_dict[col]
        else:
            # Set default values
            if col in ['volatility_index', 'pattern_volatility', 'pattern_velocity_trend',
                       'pattern_amplitude', 'pattern_asymmetry_progression', 'pattern_consistency',
                       'asymmetry_index', 'score_velocity']:
                final_dict[col] = 0.0
            elif col in ['pattern_stuttering_score', 'pattern_reading_count',
                         'patient_id', 'on_bp_medication', 'smoking_history',
                         'asymmetry_label', 'impact_tier']:
                final_dict[col] = 0
            elif col in ['pattern_type', 'response_strength', 'affected_side',
                         'age_group', 'sex', 'diabetes_type', 'bp_category']:
                final_dict[col] = 'Unknown'
            elif col in ['systolic_bp', 'diastolic_bp', 'blood_glucose']:
                final_dict[col] = 0
            elif col in ['hba1c', 'left_sensory_score', 'right_sensory_score']:
                final_dict[col] = 0.0
            elif col == 'timestamp':
                final_dict[col] = datetime.now().isoformat()
            else:
                final_dict[col] = None

    return final_dict

def run_data_pipeline(amount=5000, output_dir="master_data"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"🚀 Starting Pipeline: Generating {amount} records...")
    print("📊 Generating patients with pattern features...")

    # Generate patients
    patients = patient_gen.generate_patient_data(amount)

    print(f"✅ Generated {len(patients)} patients")

    # Flatten patient data
    print("🔄 Flattening patient data...")
    flat_data = []
    for i, patient in enumerate(patients):
        # Extract attributes from patient object
        patient_data = flatten_patient_data(patient)
        flat_data.append(patient_data)

        # Progress indicator
        if (i + 1) % 500 == 0 or i == 0 or i == len(patients) - 1:
            print(f"  Processed {i + 1}/{len(patients)} patients")

    # Create DataFrame
    master_df = pd.DataFrame(flat_data)

    # Print data summary
    print(f"\n📊 Data Summary:")
    print(f"  • Total records: {len(master_df)}")
    print(f"  • Total columns: {len(master_df.columns)}")

    # Count pattern features
    pattern_cols = [c for c in master_df.columns if c.startswith('pattern_')]
    print(f"  • Columns with pattern features: {len(pattern_cols)}")

    # Check critical columns
    critical_cols = ['volatility_index', 'asymmetry_index', 'score_velocity', 'impact_tier']
    print(f"\n🔍 Critical Column Check:")
    for col in critical_cols:
        if col in master_df.columns:
            non_null = master_df[col].notna().sum()
            min_val = master_df[col].min()
            max_val = master_df[col].max()
            print(f"  • {col}: {non_null} non-null, range: {min_val:.3f} to {max_val:.3f}")
        else:
            print(f"  • {col}: MISSING!")

    # Check pattern features
    if pattern_cols:
        print(f"\n🎯 Pattern Features Found ({len(pattern_cols)}):")
        for col in pattern_cols[:5]:
            if col in master_df.columns:
                if master_df[col].dtype != 'object':
                    mean_val = master_df[col].mean()
                    min_val = master_df[col].min()
                    max_val = master_df[col].max()
                    print(f"  • {col}: mean={mean_val:.3f}, range={min_val:.3f} to {max_val:.3f}")
                else:
                    unique_values = master_df[col].unique()[:3]
                    print(f"  • {col}: categorical, sample values={list(unique_values)}")
    else:
        print(f"\n⚠️  No pattern features found in the data!")

    # Save CSV
    csv_path = os.path.join(output_dir, "stroke_training_data.csv")
    master_df.to_csv(csv_path, index=False)

    # Save sample
    sample_path = os.path.join(output_dir, "stroke_training_sample.csv")
    if len(master_df) > 100:
        master_df.head(100).to_csv(sample_path, index=False)
        print(f"📄 Sample saved: {sample_path} (100 records)")

    print(f"\n✅ Pipeline Complete!")
    print(f"📁 Files saved in /{output_dir}")
    print(f"💾 Main CSV: {csv_path} ({len(master_df)} records)")

    # Show column info
    print(f"\n📋 All columns: {list(master_df.columns)}")

    return master_df

if __name__ == "__main__":
    print("=" * 60)
    print("🧠 LACUNAR STROKE TRAINING DATA GENERATION")
    print("=" * 60)
    print("📈 Generating 5000 patient records for model training")
    print("⏳ This may take a few minutes...")
    print("=" * 60)

    df = run_data_pipeline(amount=5000)

    # Show preview
    print(f"\n👀 Data Preview (first 3 rows):")
    print(df.head(3).to_string())

    # Check for object references
    object_columns = []
    for col in df.columns:
        sample = df[col].dropna().head(5).astype(str)
        if any('object at 0x' in str(val) for val in sample):
            object_columns.append(col)

    if object_columns:
        print(f"\n⚠️  WARNING: Found object references in columns: {object_columns}")
    else:
        print(f"\n✅ All columns contain clean data (no object references)")

    # Final statistics
    print(f"\n📊 FINAL DATASET STATISTICS:")
    print(f"  • Total patients: {len(df)}")

    # Check if we have non-zero volatility
    if 'volatility_index' in df.columns:
        non_zero_vol = df[df['volatility_index'] > 0].shape[0]
        print(f"  • Patients with non-zero volatility: {non_zero_vol} ({(non_zero_vol/len(df))*100:.1f}%)")

    if 'impact_tier' in df.columns:
        tier_counts = df['impact_tier'].value_counts().sort_index()
        print(f"  • Impact tier distribution:")
        for tier, count in tier_counts.items():
            percentage = (count / len(df)) * 100
            tier_labels = {
                0: "Normal (Strong Response)",
                1: "Mild Unilateral (Slightly Reduced)",
                2: "Moderate Unilateral (Moderately Reduced)",
                3: "Severe Unilateral (Significantly Reduced)",
                4: "Bilateral (Weak Global Response)"
            }
            label = tier_labels.get(tier, f"Tier {tier}")

            # Calculate average volatility for each tier
            if 'volatility_index' in df.columns:
                avg_vol = df[df['impact_tier'] == tier]['volatility_index'].mean()
                print(f"    - {label}: {count} patients ({percentage:.1f}%), avg volatility: {avg_vol:.3f}")
            else:
                print(f"    - {label}: {count} patients ({percentage:.1f}%)")

    print(f"\n🎯 Dataset ready for Random Forest training!")
    print("=" * 60)