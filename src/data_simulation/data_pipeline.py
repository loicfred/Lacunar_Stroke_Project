# -----------------------------------
# This pipeline is used to generate a JSON and CSV of simulated patient data.
# -----------------------------------
import os
import pandas as pd
import data_simulation.patient_generator as patient_gen

def run_data_pipeline(amount=5000, output_dir="master_data"):
    if not os.path.exists(output_dir): os.makedirs(output_dir) # Ensure output directory exists

    print(f"🚀 Starting Pipeline: Generating {amount} records...")

    # Generate a list of patients with complete sensory data
    patients = patient_gen.generate_batch_patients_data(amount)

    # Transform the list of patients into a master DataFrame
    master_df = pd.DataFrame([p.__dict__ for p in patients])

    # Save as CSV for the Random Forest
    master_df.to_csv(os.path.join(output_dir, "stroke_training_data.csv"), index=False)

    # Save as JSON for the Flask Dashboard
    # master_df.to_json(os.path.join(output_dir, "dashboard_data.json"), orient="records", indent=4)

    print(f"✅ Pipeline Complete. Files saved in /{output_dir}")


if __name__ == "__main__":
    run_data_pipeline(amount=5000)