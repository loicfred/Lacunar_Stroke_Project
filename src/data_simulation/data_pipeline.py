import os
import pandas as pd
from src.data_simulation.patient_generator import generate_patients
from src.data_simulation.sensory_simulator import generate_sensory_data

def run_data_pipeline(num_patients=1000, output_dir="master_data"):
    """
    The master pipeline to generate, merge, and save the simulation dataset.
    """
    # 1. Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print(f"🚀 Starting Pipeline: Generating {num_patients} records...")

    # 2. Generate the raw data parts
    patients = generate_patients(num_patients)
    sensory = generate_sensory_data(patients)

    # 3. Merge into a master DataFrame
    df_p = pd.DataFrame(patients)
    df_s = pd.DataFrame(sensory)
    master_df = pd.merge(df_p, df_s, on="patient_id")

    # 4. Save the "Gold Standard" datasets
    # CSV for the Random Forest / RNN models
    master_df.to_csv(os.path.join(output_dir, "stroke_training_data.csv"), index=False)

    # JSON for the Flask Dashboard
    master_df.to_json(os.path.join(output_dir, "dashboard_data.json"), orient="records", indent=4)

    print(f"✅ Pipeline Complete. Files saved in /{output_dir}")

if __name__ == "__main__":
    run_data_pipeline(num_patients=1000)