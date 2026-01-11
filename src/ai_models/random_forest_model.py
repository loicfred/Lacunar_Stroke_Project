import pandas as pd
import os
import joblib
from pyarrow import null
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# Get the location of this script
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the paths using the absolute BASE_DIR
# This points to: .../Lacunar_Stroke_Project/src/data_simulation/master_data/...
DATA_PATH = os.path.join(BASE_DIR, "data_simulation", "master_data", "stroke_training_data.csv")

# This points to: .../Lacunar_Stroke_Project/src/model/stroke_model.pkl
MODEL_SAVE_PATH = os.path.join(BASE_DIR, "model", "../../models/stroke_model.pkl")

def train_production_model():
    """
    Loads simulated data, trains a Random Forest, and saves the model.
    """
    # 1. Load the merged dataset
    if not os.path.exists(DATA_PATH):
        print(f"❌ Error: {DATA_PATH} not found. Run your data pipeline first!")
        return null()

    df = pd.read_csv(DATA_PATH)
    print(f"📊 Loaded {len(df)} records for training.")

    # 2. Select Features (X) and Multi-class Target (y)
    # Features: Left Score, Right Score, and our custom Index
    features = ['left_sensory_score', 'right_sensory_score', 'asymmetry_index']
    X = df[features]
    y = df['asymmetry_label'] # 0: Normal, 1: Unilateral, 2: Bilateral

    # 3. Split into Training and Testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Initialize and Train
    # We use 'stratify' above to ensure the 10% Bilateral cases are evenly split
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("\n" + "="*40)
    print(f"🧠 MODEL TRAINING REPORT")
    print("="*40)
    print(f"✅ Accuracy: {accuracy * 100:.2f}%")
    print("\nClassification breakdown:")
    # target_names maps the numbers back to medical terms for the report
    print(classification_report(y_test, y_pred, target_names=['Normal', 'Unilateral', 'Bilateral']))

    # 6. Save the trained 'Brain'
    # This allows the Flask app to load the model instantly
    joblib.dump(model, MODEL_SAVE_PATH)
    print(f"💾 Model saved successfully to: {MODEL_SAVE_PATH}")

    return model

if __name__ == "__main__":
    train_production_model()