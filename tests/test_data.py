import sys
import pathlib

# This finds the root directory
root_dir = pathlib.Path(__file__).parent.parent
sys.path.append(str(root_dir))


from src.data_simulation.patient_generator import generate_patients 
from src.data_simulation.sensory_simulator import generate_sensory_data

patients = generate_patients(5)
sensory_data = generate_sensory_data(patients)

print("Patient Profiles:")
for p in patients:
    print(p)

    
print()

print("\nSensory Data:")
for s in sensory_data:
    print(s)


# Convert sensory data to a lookup dictionary
sensory_lookup = {
    s["patient_id"]: s for s in sensory_data
}

# Merge patient + sensory data
final_dataset = []

for patient in patients:
    pid = patient["patient_id"]

    merged_record = {
        **patient,                     # patient profile fields
        **sensory_lookup[pid]          # sensory fields
    }

    final_dataset.append(merged_record)

# Display merged dataset
print("\nFinal Merged Dataset:")
for record in final_dataset:
    print(record)