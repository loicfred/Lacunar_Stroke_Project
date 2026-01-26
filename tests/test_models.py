import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import src.data_simulation.patient_generator as patient_gen

def run_comprehensive_test():
    print("🧪 Starting Dual-Output Model Test (Categories + Impact Tiers)...")

    # 1. GENERATE TRAINING DATA
    # We generate 500 patients to ensure the model sees enough Bilateral (10%) cases
    print("📊 Generating 500 training samples...")
    raw_patients = patient_gen.generate_batch_patients_data(500)

    df = pd.DataFrame([p.__dict__ for p in raw_patients])

    # 2. TRAIN THE MODEL
    X = df[['left_sensory_score', 'right_sensory_score', 'systolic_bp', 'hba1c', 'asymmetry_index']]
    y = df['impact_tier']

    model = RandomForestClassifier(n_estimators=200, max_depth=12, random_state=42)
    model.fit(X, y)
    print("✅ Model trained on 5-Tier Impact logic.")

    # 3. THE TRIPLE TEST (PREDICTION)
    # Define feature names to avoid the UserWarning
    cols = ['left_sensory_score', 'right_sensory_score', 'systolic_bp', 'hba1c', 'asymmetry_index']



    # 4. REPORT RESULTS
    TIER_TO_CATEGORY = {
        0: "🟢 Normal (Healthy)",
        1: "🟡 Unilateral Risk (Asymmetric)",
        2: "🟠 Unilateral Risk (Asymmetric)",
        3: "🔴 Unilateral Risk (Asymmetric)",
        4: "🟣 Bilateral Risk (Both Sides Low)"
    }

    IMPACT_LEVELS = {
        0: "Strong Response",
        1: "Slightly Reduced",
        2: "Moderately Reduced",
        3: "Significantly Reduced",
        4: "Weak Global Response"
    }

    # Updated Test Suite for Impact Tiers (0-4)
    test_cases = [
        # TIER 1: Borderline Subtle (Just enough asymmetry to trigger)
        ("Borderline Subtle", [8.5, 7.8, 80, 90, 0.08]),

        # TIER 2: Moderate Unilateral (Clear gap, but not a total loss)
        ("Moderate Gap", [9.0, 5.5, 80, 90, 0.48]),

        # TIER 3: Pronounced Unilateral (Near-complete loss on one side)
        ("Pronounced Gap", [8.8, 1.2, 80, 90, 1.52]),

        # TIER 4: Moderate Bilateral (Symmetrical but both weak - not yet "Weak Global")
        # This checks if the AI keeps it as Tier 4 because the scores are low,
        # even if they aren't at the minimum (1.0).
        ("Moderate Bilateral", [4.2, 4.4, 80, 90, 0.04]),

        # TIER 0: Healthy but Low-End (Balanced but near the 7.0 cutoff)
        ("Low-End Healthy", [7.1, 7.2, 80, 90, 0.01]),

        ("my test case", [6.91, 6.98, 80, 90, 0.01])
    ]

    print("\n" + "="*65)
    print(f"{'TEST CASE':<20} | {'IMPAIRMENT CATEGORY':<25} | {'IMPACT LEVEL'}")
    print("-" * 65)

    for name, values in test_cases:
        test_df = pd.DataFrame([values], columns=cols)

        # The model predicts the Tier (0-4)
        tier_pred = model.predict(test_df)[0]

        category = TIER_TO_CATEGORY[tier_pred]
        impact = IMPACT_LEVELS[tier_pred]

        print(f"{name:<20} | {category:<25} | {impact}")

    print("="*65)

    # 5. ANALYZE FEATURE IMPORTANCE
    importances = model.feature_importances_
    print("\n💡 Feature Importance Breakdown (Tiers are sensitive to both Index and Scores):")
    for feature, importance in zip(cols, importances):
        print(f"- {feature.replace('_', ' ').title():<18}: {importance:.2%}")

if __name__ == "__main__":
    run_comprehensive_test()

