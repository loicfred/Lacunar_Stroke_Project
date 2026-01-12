import pandas as pd
import os
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Get the location of this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the paths
DATA_PATH = os.path.join(BASE_DIR, "data_simulation", "master_data", "stroke_training_data.csv")
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "model", "stroke_model.pkl")

# IMPACT LEVEL MAPPING (For the report)
IMPACT_LEVELS = {
    0: "Strong Response",
    1: "Slightly Reduced",
    2: "Moderately Reduced",
    3: "Significantly Reduced",
    4: "Weak Global Response"
}

def train_production_model():
    """
    Trains a Random Forest to predict specific Impact Tiers.
    """
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"📊 Loaded {len(df)} records for training.")

    # 1. Select Features (X)
    features = ['left_sensory_score', 'right_sensory_score', 'asymmetry_index']
    X = df[features]

    # 2. Select Target (y)
    # Ensure your CSV has this 'impact_tier' column (0-4)
    # If your column is named differently, change it here:
    y = df['impact_tier']

    # 3. Split into Training and Testing sets
    # Stratify ensures each Tier (0-4) is represented in both sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Initialize and Train
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "="*45)
    print(f"🧠 AI IMPACT ANALYSIS REPORT")
    print("="*45)
    print(f"✅ Overall Accuracy: {accuracy * 100:.2f}%")
    print("\nTier Breakdown:")

    # Map the numbers 0-4 to your new Impact Level names
    target_names = [IMPACT_LEVELS[i] for i in sorted(y.unique())]
    print(classification_report(y_test, y_pred, target_names=target_names))

    # 6. Save the trained 'Brain'
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model with Tiers saved to: {MODEL_SAVE_PATH}")

    return model

if __name__ == "__main__":
    train_production_model()