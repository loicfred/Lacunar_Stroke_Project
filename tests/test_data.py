import sys
import pathlib
import os
import pandas as pd
import json

# --- 1. SETUP SYSTEM PATH ---
# Ensures 'src' is findable from the /tests/ folder
root_dir = pathlib.Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Now import from your modules
from src.data_simulation.patient_generator import generate_patients
from src.data_simulation.sensory_simulator import generate_sensory_data

def run_test():
    # --- 2. GENERATE DATA ---
    print("🔄 Generating 5 patient profiles...")
    patients = generate_patients(5)

    print("🔄 Generating bilateral sensory data...")
    # This uses the logic we built: asymmetry index, severity, and side labels
    sensory_data = generate_sensory_data(patients)

    # --- 3. MERGE DATA USING PANDAS ---
    # Convert lists of dictionaries to DataFrames for easy merging
    df_patients = pd.DataFrame(patients)
    df_sensory = pd.DataFrame(sensory_data)

    # Perform the merge on patient_id
    merged_df = pd.merge(df_patients, df_sensory, on="patient_id")

    # --- 4. PREPARE EXPORT DIRECTORY ---
    # Ensure the /data/ folder exists so the script doesn't crash
    data_dir = os.path.join(root_dir, "data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"📁 Created directory: {data_dir}")

    # --- 5. EXPORT FILES ---
    # A. CSV for AI Training (Scikit-Learn/Random Forest)
    csv_path = os.path.join(data_dir, "stroke_training_data.csv")
    merged_df.to_csv(csv_path, index=False)

    # B. JSON for Flask App (Dashboard/Frontend)
    json_path = os.path.join(data_dir, "patient_dashboard_data.json")
    # 'records' orientation creates a list of dicts: [{p1}, {p2}...]
    merged_df.to_json(json_path, orient="records", indent=4)

    # --- 6. DISPLAY RESULTS ---
    print("\n" + "="*50)
    print("✅ SUCCESS: DATA MERGED AND EXPORTED")
    print("="*50)
    print(f"📍 CSV Path: {csv_path}")
    print(f"📍 JSON Path: {json_path}")
    print("\nPreview of first 2 records:")
    print(merged_df.head(4).to_string())

if __name__ == "__main__":
    run_test()