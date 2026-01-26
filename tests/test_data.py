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
import src.data_simulation.patient_generator as patient_gen

def run_test():
    # --- 1. GENERATE DATA ---
    print("🔄 Generating 5 complete patient profiles...")

    # 2. Generate the raw data parts
    patients = patient_gen.generate_batch_patients_data(20)

    # 3. Merge into a master DataFrame
    merged_df = pd.DataFrame([p.__dict__ for p in patients])

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
    #json_path = os.path.join(data_dir, "patient_dashboard_data.json")
    # 'records' orientation creates a list of dicts: [{p1}, {p2}...]
    #merged_df.to_json(json_path, orient="records", indent=4)

    # --- 6. DISPLAY RESULTS ---
    print("\n" + "="*50)
    print("✅ SUCCESS: DATA MERGED AND EXPORTED")
    print("="*50)
    print(f"📍 CSV Path: {csv_path}")
    #print(f"📍 JSON Path: {json_path}")
    print("\nPreview of first 5 records:")
    print(merged_df.head(20).to_string())

if __name__ == "__main__":
    run_test()