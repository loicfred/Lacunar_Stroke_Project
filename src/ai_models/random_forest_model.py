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

# --- Clinical Mappings ---
IMPACT_LEVELS = {
    0: "Strong Response",
    1: "Slightly Reduced",
    2: "Moderately Reduced",
    3: "Significantly Reduced",
    4: "Weak Global Response"
}

TIER_TO_CATEGORY = {
    0: "🟢 Normal (Healthy)",
    1: "🟡 Unilateral Risk (Asymmetric)",
    2: "🟠 Unilateral Risk (Asymmetric)",
    3: "🔴 Unilateral Risk (Asymmetric)",
    4: "🟣 Bilateral Risk (Both Sides Low)"
}


def train_production_model():
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)
    print(f"📊 Loaded {len(df)} records for training.")

    features = ['left_sensory_score', 'right_sensory_score', 'asymmetry_index']
    X = df[features]
    y = df['impact_tier']

    # Split using stratification to ensure Tier 4 is balanced
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train with hyperparameters from test_models
    model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    print(f"✅ Training Complete. Test Accuracy: {accuracy_score(y_test, y_pred)*100:.2f}%")

    # Detailed report
    unique_tiers = sorted(y.unique())
    target_names = [IMPACT_LEVELS[t] for t in unique_tiers]
    print("\nDetailed Classification Metrics:")
    print(classification_report(y_test, y_pred, target_names=target_names))


    # Save the model
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model saved successfully to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    train_production_model()