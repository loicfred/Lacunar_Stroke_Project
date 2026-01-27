import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import src.data_simulation.patient_generator as patient_gen
import math

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
    print("🧪 Starting Dual-Output Model Test with Pattern Features...")

    # 1. GENERATE TRAINING DATA WITH PATTERN FEATURES
    print("📊 Generating 5000 training samples with pattern features...")
    raw_patients = patient_gen.generate_patient_data(
        5000
    )

    # Convert to DataFrame with enhanced features
    df_data = []
    for p in raw_patients:
        patient_dict = p.__dict__.copy()

        # Calculate asymmetry index if not present
        if 'asymmetry_index' not in patient_dict:
            left = patient_dict.get('left_sensory_score', 9.0)
            right = patient_dict.get('right_sensory_score', 9.0)
            avg = (left + right) / 2
            patient_dict['asymmetry_index'] = abs(left - right) / (avg + 1)

        # Add pattern features if available
        if hasattr(p, 'pattern_features'):
            pattern_features = p.pattern_features
            for key, value in pattern_features.items():
                if key != 'pattern_type':  # Skip categorical
                    patient_dict[f'pattern_{key}'] = value

        # Add missing features with defaults
        patient_dict.setdefault('diastolic_bp', 80)
        patient_dict.setdefault('blood_glucose', 100)
        patient_dict.setdefault('diabetes_type', 'None')
        patient_dict.setdefault('bp_category', 'Normal')
        patient_dict.setdefault('on_bp_medication', 0)

        df_data.append(patient_dict)

    df = pd.DataFrame(df_data)

    # Encode categorical variables
    df['diabetes_type_encoded'] = df['diabetes_type'].apply(encode_diabetes_type)
    df['bp_category_encoded'] = df['bp_category'].apply(encode_bp_category)

    # Define enhanced feature set with pattern features
    base_features = [
        'left_sensory_score',
        'right_sensory_score',
        'asymmetry_index',
        'systolic_bp',
        'diastolic_bp',
        'hba1c',
        'blood_glucose',
        'diabetes_type_encoded',
        'bp_category_encoded',
        'on_bp_medication',
        'smoking_history',
        'score_velocity',
        'volatility_index'
    ]

    # Add pattern features if they exist
    pattern_feature_prefixes = ['pattern_volatility_index', 'pattern_velocity_trend',
                                'pattern_stuttering_score', 'pattern_pattern_amplitude',
                                'pattern_asymmetry_progression', 'pattern_consistency_score']

    features = base_features.copy()
    for pattern_feature in pattern_feature_prefixes:
        if pattern_feature in df.columns:
            features.append(pattern_feature)
            print(f"✅ Added pattern feature: {pattern_feature}")

    print(f"📊 Total features: {len(features)}")

    # Ensure all features exist in dataframe
    for feature in features:
        if feature not in df.columns:
            print(f"⚠️  Warning: Feature '{feature}' not found, adding with default value 0")
            df[feature] = 0

    # Convert all features to numeric
    for feature in features:
        df[feature] = pd.to_numeric(df[feature], errors='coerce')

    # Handle NaN values
    df = df.dropna(subset=features + ['impact_tier'])

    X = df[features]
    y = df['impact_tier']

    print(f"\n📊 Dataset shape: {X.shape}")
    print(f"🎯 Classes: {sorted(y.unique())}")

    model = RandomForestClassifier(n_estimators=300, max_depth=18, random_state=42)
    model.fit(X, y)
    print("✅ Model trained on enhanced feature set.")

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

    # 4. UPDATED TEST SUITE with pattern features
    test_cases = [
        ("Subtle Asymmetry", [
            8.5, 7.8, 0.08,  # Left, Right, AsymIndex
            135, 80, 5.8, 100,  # SBP, DBP, HbA1c, Blood Glucose
            0, 0, 0,  # Diabetes type (None=0), BP category (Normal=0), On BP Med (No=0)
            0, -0.001, 0.8,  # Smoking, Velocity, Volatility
            0.5, -0.002, 1, 0.3, 0.001, 0.8  # Pattern features
        ]),
        ("High BP Stroke", [
            9.0, 5.5, 0.48,  # Left, Right, AsymIndex
            175, 105, 6.2, 120,  # SBP, DBP, HbA1c, Blood Glucose
            0, 3, 1,  # No diabetes, Hypertension Stage 2, On BP Med
            1, -0.012, 2.2,  # Smoking, Velocity, Volatility
            2.1, -0.015, 3, 1.8, 0.005, 0.6  # Pattern features
        ]),
        ("Severe Diabetic", [
            8.8, 1.2, 1.52,  # Left, Right, AsymIndex
            150, 90, 8.5, 250,  # SBP, DBP, HbA1c, Blood Glucose
            2, 2, 1,  # Type 2 Diabetes, Hypertension Stage 1, On BP Med
            0, -0.025, 2.8,  # No smoking, Velocity, Volatility
            2.5, -0.020, 4, 2.2, 0.008, 0.5  # Pattern features
        ]),
        ("Global Weakness", [
            4.2, 4.4, 0.04,  # Left, Right, AsymIndex
            140, 85, 7.0, 180,  # SBP, DBP, HbA1c, Blood Glucose
            0, 1, 0,  # No diabetes, Elevated BP, Not on BP Med
            1, -0.015, 1.8,  # Smoking, Velocity, Volatility
            1.2, -0.010, 2, 1.5, 0.003, 0.7  # Pattern features
        ]),
        ("Healthy Baseline", [
            9.1, 9.2, 0.01,  # Left, Right, AsymIndex
            120, 78, 5.2, 95,  # SBP, DBP, HbA1c, Blood Glucose
            0, 0, 0,  # No diabetes, Normal BP, Not on BP Med
            0, 0.000, 0.3,  # No smoking, Velocity, Volatility
            0.2, 0.001, 0, 0.1, 0.000, 0.9  # Pattern features
        ]),
        ("Lacunar Pattern", [
            7.5, 6.0, 0.22,  # Left, Right, AsymIndex
            145, 88, 6.0, 110,  # SBP, DBP, HbA1c, Blood Glucose
            0, 2, 0,  # No diabetes, Hypertension Stage 1, Not on BP Med
            1, -0.008, 1.8,  # Smoking, Velocity, Volatility
            1.8, -0.005, 3, 1.2, 0.004, 0.6  # Pattern features (high stuttering)
        ])
    ]

    print("\n" + "="*100)
    print(f"{'TEST CASE':<20} | {'IMPAIRMENT CATEGORY':<25} | {'IMPACT LEVEL':<25} | {'TIER':<5} | {'PATTERN'}")
    print("-" * 100)

    for name, values in test_cases:
        test_df = pd.DataFrame([values], columns=features)
        tier_pred = model.predict(test_df)[0]
        probs = model.predict_proba(test_df)[0]
        confidence = max(probs)

        category = TIER_TO_CATEGORY.get(tier_pred, "Unknown")
        impact = IMPACT_LEVELS.get(tier_pred, "Unknown")

        # Check pattern features
        stuttering_score = values[features.index('pattern_stuttering_score')] if 'pattern_stuttering_score' in features else 0
        pattern_type = "stable"
        if stuttering_score >= 3:
            pattern_type = "HIGH stuttering"
        elif stuttering_score >= 2:
            pattern_type = "MODERATE stuttering"
        elif stuttering_score >= 1:
            pattern_type = "mild stuttering"

        print(f"{name:<20} | {category:<25} | {impact:<25} | {tier_pred:<5} | {pattern_type} (Conf: {confidence:.1%})")

    print("="*100)

    # 5. FEATURE IMPORTANCE
    importances = model.feature_importances_
    print("\n💡 Feature Importance (How the model makes decisions):")
    feature_names_display = []
    for feat in features:
        if feat.startswith('pattern_'):
            display_name = feat.replace('pattern_', '').replace('_', ' ').title() + ' (Pattern)'
        else:
            display_name = feat.replace('_', ' ').title()
        feature_names_display.append(display_name)

    for feature, importance in sorted(zip(feature_names_display, importances), key=lambda x: x[1], reverse=True):
        print(f"- {feature:<30}: {importance:.2%}")

    # 6. PATTERN FEATURE ANALYSIS
    print("\n🎯 Pattern Feature Analysis:")
    pattern_features = [f for f in features if f.startswith('pattern_')]
    if pattern_features:
        for pattern_feat in pattern_features:
            feat_importance = importances[features.index(pattern_feat)]
            print(f"- {pattern_feat.replace('pattern_', '').replace('_', ' ').title():<25}: {feat_importance:.3%}")
    else:
        print("⚠️  No pattern features found in the model")

    # 7. ACCURACY ON TRAINING DATA
    y_pred = model.predict(X)
    accuracy = (y_pred == y).mean()
    print(f"\n📊 Training Accuracy: {accuracy:.2%}")

    # Class distribution
    print("\n📈 Class Distribution:")
    class_counts = y.value_counts().sort_index()
    for tier, count in class_counts.items():
        category = TIER_TO_CATEGORY.get(tier, f"Tier {tier}")
        print(f"- {category}: {count} samples ({count/len(y):.1%})")

if __name__ == "__main__":
    run_comprehensive_test()