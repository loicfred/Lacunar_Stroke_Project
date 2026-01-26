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

IMPACT_LEVELS = {
    0: "Strong Response",
    1: "Slightly Reduced",
    2: "Moderately Reduced",
    3: "Significantly Reduced",
    4: "Weak Global Response"
}

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

    features = [
        'left_sensory_score',
        'right_sensory_score',
        'asymmetry_index',
        'systolic_bp',      # Continuous (Ref 5)
        'hba1c',            # Continuous (Ref 6)
        'smoking_history',
        'score_velocity',
        'volatility_index'  # Stuttering pattern (Ref 3)
    ]

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

    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model saved successfully to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_production_model()