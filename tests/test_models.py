import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import src.data_simulation.patient_generator as patient_gen

# Encoding functions (same as in app.py)
def encode_diabetes_type(diabetes_type):
    """Encode diabetes type to numerical values"""
    encoding = {
        "None": 0,
        "Type 1": 1,
        "Type 2": 2,
        "Gestational": 3,
        "Prediabetes": 4,
        "Other": 5
    }
    return encoding.get(diabetes_type, 0)

def encode_bp_category(bp_category):
    """Encode BP category to numerical values"""
    encoding = {
        "Normal": 0,
        "Elevated": 1,
        "Hypertension Stage 1": 2,
        "Hypertension Stage 2": 3,
        "Hypertensive Crisis": 4
    }
    return encoding.get(bp_category, 0)

def run_comprehensive_test():
    print("🧪 Starting Dual-Output Model Test...")

    # 1. GENERATE TRAINING DATA
    print("📊 Generating 5000 training samples...")
    raw_patients = patient_gen.generate_batch_patients_data(5000)

    # Convert objects to DataFrame
    df_data = []
    for p in raw_patients:
        # Get all attributes from Patient object
        patient_dict = p.__dict__.copy()

        # Calculate asymmetry index if not present
        if 'asymmetry_index' not in patient_dict:
            left = patient_dict.get('left_sensory_score', 9.0)
            right = patient_dict.get('right_sensory_score', 9.0)
            avg = (left + right) / 2
            patient_dict['asymmetry_index'] = abs(left - right) / (avg + 1)

        # Add missing features with defaults if needed
        patient_dict.setdefault('diastolic_bp', 80)
        patient_dict.setdefault('blood_glucose', 100)
        patient_dict.setdefault('diabetes_type', 'None')
        patient_dict.setdefault('bp_category', 'Normal')
        patient_dict.setdefault('on_bp_medication', 0)

        df_data.append(patient_dict)

    df = pd.DataFrame(df_data)

    # 2. ALIGN FEATURES WITH UPDATED PRODUCTION MODEL (13 features)
    # Encode categorical variables
    df['diabetes_type_encoded'] = df['diabetes_type'].apply(encode_diabetes_type)
    df['bp_category_encoded'] = df['bp_category'].apply(encode_bp_category)

    cols = [
        'left_sensory_score',
        'right_sensory_score',
        'asymmetry_index',
        'systolic_bp',
        'diastolic_bp',        # NEW
        'hba1c',
        'blood_glucose',       # NEW
        'diabetes_type_encoded',  # NEW (encoded)
        'bp_category_encoded',    # NEW (encoded)
        'on_bp_medication',    # NEW
        'smoking_history',
        'score_velocity',
        'volatility_index'
    ]

    # Ensure all columns exist
    for col in cols:
        if col not in df.columns:
            if col == 'diabetes_type_encoded':
                df[col] = df['diabetes_type'].apply(encode_diabetes_type)
            elif col == 'bp_category_encoded':
                df[col] = df['bp_category'].apply(encode_bp_category)
            else:
                df[col] = 0  # Default value for missing columns

    X = df[cols]
    y = df['impact_tier']

    model = RandomForestClassifier(n_estimators=300, max_depth=18, random_state=42)
    model.fit(X, y)
    print(f"✅ Model trained on {len(cols)} physiological features.")

    # 3. MAPPING
    TIER_TO_CATEGORY = {
        0: "🟢 Normal (Healthy)",
        1: "🟡 Unilateral Risk",
        2: "🟠 Unilateral Risk",
        3: "🔴 Unilateral Risk",
        4: "🟣 Bilateral Risk"
    }

    IMPACT_LEVELS = {
        0: "Strong Response",
        1: "Slightly Reduced",
        2: "Moderately Reduced",
        3: "Significantly Reduced",
        4: "Weak Global Response"
    }

    # 4. UPDATED TEST SUITE (Now with 13 values per case)
    # Order matches the cols list above
    test_cases = [
        ("Subtle Asymmetry", [
            8.5, 7.8, 0.08,  # Left, Right, AsymIndex
            135, 80, 5.8, 100,  # SBP, DBP, HbA1c, Blood Glucose
            0, 0, 0,  # Diabetes type (None=0), BP category (Normal=0), On BP Med (No=0)
            0, -0.001, 0.8  # Smoking, Velocity, Volatility
        ]),
        ("High BP Stroke", [
            9.0, 5.5, 0.48,  # Left, Right, AsymIndex
            175, 105, 6.2, 120,  # SBP, DBP, HbA1c, Blood Glucose
            0, 3, 1,  # No diabetes, Hypertension Stage 2, On BP Med
            1, -0.012, 2.2  # Smoking, Velocity, Volatility
        ]),
        ("Severe Diabetic", [
            8.8, 1.2, 1.52,  # Left, Right, AsymIndex
            150, 90, 8.5, 250,  # SBP, DBP, HbA1c, Blood Glucose
            2, 2, 1,  # Type 2 Diabetes, Hypertension Stage 1, On BP Med
            0, -0.025, 2.8  # No smoking, Velocity, Volatility
        ]),
        ("Global Weakness", [
            4.2, 4.4, 0.04,  # Left, Right, AsymIndex
            140, 85, 7.0, 180,  # SBP, DBP, HbA1c, Blood Glucose
            0, 1, 0,  # No diabetes, Elevated BP, Not on BP Med
            1, -0.015, 1.8  # Smoking, Velocity, Volatility
        ]),
        ("Healthy Baseline", [
            9.1, 9.2, 0.01,  # Left, Right, AsymIndex
            120, 78, 5.2, 95,  # SBP, DBP, HbA1c, Blood Glucose
            0, 0, 0,  # No diabetes, Normal BP, Not on BP Med
            0, 0.000, 0.3  # No smoking, Velocity, Volatility
        ]),
        ("Borderline Case", [
            8.0, 7.0, 0.13,  # Left, Right, AsymIndex
            145, 92, 6.4, 110,  # SBP, DBP, HbA1c, Blood Glucose
            4, 2, 0,  # Prediabetes, Hypertension Stage 1, Not on BP Med
            1, -0.005, 1.2  # Smoking, Velocity, Volatility
        ])
    ]

    print("\n" + "="*90)
    print(f"{'TEST CASE':<20} | {'IMPAIRMENT CATEGORY':<25} | {'IMPACT LEVEL':<25} | {'TIER'}")
    print("-" * 90)

    for name, values in test_cases:
        test_df = pd.DataFrame([values], columns=cols)
        tier_pred = model.predict(test_df)[0]
        probs = model.predict_proba(test_df)[0]
        confidence = max(probs)

        category = TIER_TO_CATEGORY.get(tier_pred, "Unknown")
        impact = IMPACT_LEVELS.get(tier_pred, "Unknown")

        print(f"{name:<20} | {category:<25} | {impact:<25} | {tier_pred} (Conf: {confidence:.1%})")

    print("="*90)

    # 5. FEATURE IMPORTANCE
    importances = model.feature_importances_
    print("\n💡 Feature Importance (How the model makes decisions):")
    feature_names_display = [
        'Left Sensory Score', 'Right Sensory Score', 'Asymmetry Index',
        'Systolic BP', 'Diastolic BP', 'HbA1c', 'Blood Glucose',
        'Diabetes Type', 'BP Category', 'On BP Medication',
        'Smoking History', 'Score Velocity', 'Volatility Index'
    ]

    for feature, importance in sorted(zip(feature_names_display, importances), key=lambda x: x[1], reverse=True):
        print(f"- {feature:<18}: {importance:.2%}")

    # 6. MODEL ACCURACY CHECK
    print("\n📊 Model Performance Check:")
    y_pred = model.predict(X)
    accuracy = (y_pred == y).mean()
    print(f"- Training Accuracy: {accuracy:.2%}")

    # Class distribution
    print("\n📈 Class Distribution in Training Data:")
    class_counts = y.value_counts().sort_index()
    for tier, count in class_counts.items():
        category = TIER_TO_CATEGORY.get(tier, f"Tier {tier}")
        print(f"- {category}: {count} samples ({count/len(y):.1%})")

if __name__ == "__main__":
    run_comprehensive_test()