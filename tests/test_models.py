import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from src.data_simulation.patient_generator import generate_patients
from src.data_simulation.sensory_simulator import generate_sensory_data

def run_comprehensive_test():
    print("🧪 Starting Multi-Class Model Test (Normal vs. Unilateral vs. Bilateral)...")

    # 1. GENERATE TRAINING DATA
    # We generate 500 patients to ensure the model sees enough Bilateral (10%) cases
    print("📊 Generating 500 training samples...")
    raw_patients = generate_patients(500)
    # Using our new logic with asymmetric_probability=0.4 and bilateral_probability=0.1
    raw_sensory = generate_sensory_data(raw_patients)

    df = pd.DataFrame(raw_sensory)

    # 2. TRAIN THE MODEL
    X = df[['left_sensory_score', 'right_sensory_score', 'asymmetry_index']]
    y = df['asymmetry_label'] # Now contains 0, 1, and 2

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    print("✅ Model trained on 3-class logic.")

    # 3. THE TRIPLE TEST (PREDICTION)
    # Define feature names to avoid the UserWarning
    cols = ['left_sensory_score', 'right_sensory_score', 'asymmetry_index']

    # Patient A: Healthy (High & Balanced)
    p_normal = pd.DataFrame([[9.2, 9.4, 0.02]], columns=cols)

    # Patient B: Unilateral/Stroke Risk (Lopsided)
    p_unilateral = pd.DataFrame([[9.0, 4.1, 0.74]], columns=cols)

    # Patient C: Bilateral/Systemic Risk (Both Low)
    p_bilateral = pd.DataFrame([[3.2, 3.0, 0.06]], columns=cols)

    # Run Predictions
    pred_a = model.predict(p_normal)[0]
    pred_b = model.predict(p_unilateral)[0]
    pred_c = model.predict(p_bilateral)[0]

    # 4. REPORT RESULTS
    results_map = {
        0: "🟢 Normal (Healthy)",
        1: "🟡 Unilateral Risk (Asymmetric)",
        2: "🔴 Bilateral Risk (Both Sides Low)"
    }

    print("\n" + "="*40)
    print("      AI PREDICTION RESULTS")
    print("="*40)
    print(f"Patient A (9.2, 9.4): {results_map[pred_a]}")
    print(f"Patient B (9.0, 4.1): {results_map[pred_b]}")
    print(f"Patient C (3.2, 3.0): {results_map[pred_c]}")
    print("="*40)

    # 5. ANALYZE FEATURE IMPORTANCE
    importances = model.feature_importances_
    print("\n💡 Feature Importance Breakdown:")
    print(f"- Left Score:      {importances[0]:.2%}")
    print(f"- Right Score:     {importances[1]:.2%}")
    print(f"- Asymmetry Index: {importances[2]:.2%}")

if __name__ == "__main__":
    run_comprehensive_test()