import pandas as pd
import os
import joblib
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data_simulation", "master_data", "stroke_training_data.csv")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "model", "stroke_model.pkl")

DIABETES_TYPE_ENCODING = {
    "None": 0,
    "Type 1": 1,
    "Type 2": 2,
    "Gestational": 3,
    "Prediabetes": 4,
    "Other": 5
}

BP_CATEGORY_ENCODING = {
    "Normal": 0,
    "Elevated": 1,
    "Hypertension Stage 1": 2,
    "Hypertension Stage 2": 3,
    "Hypertensive Crisis": 4
}

IMPACT_LEVELS = {
    0: "Strong Response",
    1: "Slightly Reduced",
    2: "Moderately Reduced",
    3: "Significantly Reduced",
    4: "Weak Global Response"
}

def encode_categorical_features(df):
    """Encode categorical string columns to numeric values."""
    df_encoded = df.copy()

    # Encode diabetes_type
    if 'diabetes_type' in df_encoded.columns:
        df_encoded['diabetes_type'] = df_encoded['diabetes_type'].map(
            lambda x: DIABETES_TYPE_ENCODING.get(x, 0)
        )

    # Encode bp_category
    if 'bp_category' in df_encoded.columns:
        df_encoded['bp_category'] = df_encoded['bp_category'].map(
            lambda x: BP_CATEGORY_ENCODING.get(x, 0)
        )

    # Encode on_bp_medication (NEW)
    if 'on_bp_medication' in df_encoded.columns:
        df_encoded['on_bp_medication'] = df_encoded['on_bp_medication'].apply(
            lambda x: encode_bp_medication(x)
        )

    return df_encoded

def encode_bp_medication(bp_med_status):
    """Encode BP medication status to numerical values"""
    if isinstance(bp_med_status, str):
        encoding = {
            "No": 0,
            "Yes": 1,
            "Irregular": 2,
            "0": 0,
            "1": 1,
            "2": 2
        }
        return encoding.get(bp_med_status, 0)
    else:
        # If it's already a number, ensure it's 0, 1, or 2
        return int(bp_med_status) if bp_med_status in [0, 1, 2] else 0

def train_production_model():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)

    # Calculate Volatility Index if not in CSV (Ref 3)
    # Stuttering Pattern: SD of last 5 readings
    if 'volatility_index' not in df.columns:
        # Simulating volatility for training data consistency
        df['volatility_index'] = df.apply(lambda x: np.random.uniform(0.1, 2.5) if x['impact_tier'] > 0 else np.random.uniform(0, 0.3), axis=1)

    # Check for pattern features in the dataset
    pattern_columns = [col for col in df.columns if col.startswith('pattern_')]
    print(f"🔍 Found {len(pattern_columns)} pattern features: {pattern_columns}")

    df = encode_categorical_features(df)

    # Define base features
    base_features = [
        'left_sensory_score',
        'right_sensory_score',
        'asymmetry_index',
        'systolic_bp',
        'diastolic_bp',
        'hba1c',
        'blood_glucose',
        'diabetes_type',
        'bp_category',
        'on_bp_medication',
        'smoking_history',
        'score_velocity', #To detect progressive deterioration
        'volatility_index' #Stuttering pattern (fluctuation pattern of sensory readings over multiple measurements)
    ]

    # Add available pattern features
    features = base_features.copy()
    for pattern_col in pattern_columns:
        if pattern_col in df.columns:
            features.append(pattern_col)

    print(f"\n📋 Training with {len(features)} features:")
    for i, feat in enumerate(features, 1):
        print(f"  {i:2d}. {feat}")

    # Ensure all features are numeric
    for feature in features:
        if feature in df.columns:
            df[feature] = pd.to_numeric(df[feature], errors='coerce')

    # Check data types
    print("\n📊 Feature Data Types:")
    for feature in features:
        if feature in df.columns:
            print(f"  - {feature}: {df[feature].dtype}")

    X = df[features]
    y = df['impact_tier']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(n_estimators=300, max_depth=18, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print(f"✅ Training Complete. Test Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")

    unique_tiers = sorted(y.unique())
    target_names = [IMPACT_LEVELS[t] for t in unique_tiers]
    print(classification_report(y_test, y_pred, target_names=target_names))

    # Feature importance
    print("\n💡 Feature Importance:")
    importances = model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': features,
        'importance': importances
    }).sort_values('importance', ascending=False)

    for _, row in feature_importance.iterrows():
        print(f"  - {row['feature']}: {row['importance']:.3%}")


    print("\n🎯 Pattern Feature Importance Analysis:")
    pattern_importances = []
    for i, (feature, importance) in enumerate(zip(features, model.feature_importances_)):
        if feature.startswith('pattern_'):
            pattern_importances.append((feature, importance))

    # Sort pattern features by importance
    for feature, importance in sorted(pattern_importances, key=lambda x: x[1], reverse=True):
        print(f"  - {feature}: {importance:.3%}")


    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model saved successfully to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_production_model()