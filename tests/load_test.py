import joblib
import pandas as pd
import os

# 1. SETUP PATHS
# This finds the absolute path to your project root (Lacunar_Stroke_Project)
# because this script is likely in a subfolder like /tests/ or /src/ai_models/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "src", "model", "stroke_model.pkl")

def run_comprehensive_load_test():
    print("🔍 Attempting to load the trained AI Model...")
    print(f"📍 Looking at: {MODEL_PATH}")

    # 2. CHECK IF FILE EXISTS
    if not os.path.exists(MODEL_PATH):
        print("❌ ERROR: 'stroke_model.pkl' not found!")
        print("Please ensure you ran random_forest_model.py successfully first.")
        return

    # 3. LOAD THE MODEL
    try:
        model = joblib.load(MODEL_PATH)
        print("✅ Model loaded successfully into memory!\n")
    except Exception as e:
        print(f"❌ ERROR: Failed to load the model file. {e}")
        return

    # 4. DEFINE NEW TEST DATA
    # We use pd.DataFrame with column names to avoid the UserWarning
    cols = ['left_sensory_score', 'right_sensory_score', 'asymmetry_index']

    test_cases = [
        {
            "name": "Severe Bilateral (Both sides low)",
            "data": pd.DataFrame([[2.1, 2.0, 0.0488]], columns=cols)
        },
        {
            "name": "Mild Unilateral (One-sided)",
            "data": pd.DataFrame([[8.2, 6.5, 0.2313]], columns=cols)
        },
        {
            "name": "Borderline Normal (Balanced)",
            "data": pd.DataFrame([[6.8, 6.9, 0.0146]], columns=cols)
        }
    ]

    # 5. RUN PREDICTIONS
    results_map = {
        0: "🟢 NORMAL",
        1: "🟡 UNILATERAL RISK (Stroke Pattern A)",
        2: "🔴 BILATERAL RISK (Stroke Pattern B)"
    }

    print("="*45)
    print(f"{'PATIENT TYPE':<25} | {'AI PREDICTION'}")
    print("-" * 45)

    for case in test_cases:
        prediction = model.predict(case["data"])[0]
        label = results_map[prediction]
        print(f"{case['name']:<25} | {label}")

    print("="*45)

if __name__ == "__main__":
    run_comprehensive_load_test()