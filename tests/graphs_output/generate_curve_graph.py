import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_curve, auc
from sklearn.preprocessing import label_binarize

# --- STEP 1: DYNAMIC PATH RESOLUTION ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
POTENTIAL_PATHS = [
    os.path.join(SCRIPT_DIR, "stroke_training_data.csv"),
    os.path.join(os.path.dirname(os.path.dirname(SCRIPT_DIR)), "src", "data_simulation", "master_data", "stroke_training_data.csv"),
    "stroke_training_data.csv"
]

DATA_PATH = next((p for p in POTENTIAL_PATHS if os.path.exists(p)), None)

if not DATA_PATH:
    print("❌ Error: 'stroke_training_data.csv' not found.")
    exit()

# --- STEP 2: LOAD AND PREPROCESS DATA ---
df = pd.read_csv(DATA_PATH)

DIABETES_ENCODING = {"None": 0, "Type 1": 1, "Type 2": 2, "Gestational": 3, "Prediabetes": 4, "Other": 5}
BP_ENCODING = {"Normal": 0, "Elevated": 1, "Hypertension Stage 1": 2, "Hypertension Stage 2": 3, "Hypertensive Crisis": 4}
IMPACT_LEVELS = {
    0: "Strong Response",
    1: "Slightly Reduced",
    2: "Moderately Reduced",
    3: "Significantly Reduced",
    4: "Weak Global Response"
}

if df['diabetes_type'].dtype == 'O':
    df['diabetes_type'] = df['diabetes_type'].map(DIABETES_ENCODING).fillna(0)
if df['bp_category'].dtype == 'O':
    df['bp_category'] = df['bp_category'].map(BP_ENCODING).fillna(0)
if 'pattern_type' in df.columns and df['pattern_type'].dtype == 'O':
    df['pattern_type'] = pd.factorize(df['pattern_type'])[0]

features = [
    'left_sensory_score', 'right_sensory_score', 'asymmetry_index', 'systolic_bp', 'diastolic_bp',
    'hba1c', 'blood_glucose', 'diabetes_type', 'bp_category', 'on_bp_medication',
    'smoking_history', 'score_velocity', 'volatility_index', 'pattern_volatility',
    'pattern_velocity_trend', 'pattern_stuttering_score', 'pattern_amplitude',
    'pattern_asymmetry_progression', 'pattern_type', 'pattern_consistency', 'pattern_reading_count'
]

for col in features:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

X = df[features]
y = df['impact_tier']

# --- STEP 3: MODEL TRAINING ---
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=300, max_depth=18, random_state=42)
model.fit(X_train, y_train)

# --- STEP 4: INDIVIDUAL ROC CALCULATION & PLOTTING ---
y_test_bin = label_binarize(y_test, classes=sorted(y.unique()))
y_score = model.predict_proba(X_test)
n_classes = y_test_bin.shape[1]

# Create a grid of subplots (2 rows, 3 columns to fit 5 tiers)
fig, axes = plt.subplots(nrows=2, ncols=3, figsize=(18, 12), dpi=300)
axes = axes.flatten()
colors = ['#2E86C1', '#CB4335', '#28B463', '#D68910', '#884EA0']

for i in range(n_classes):
    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
    roc_auc = auc(fpr, tpr)

    ax = axes[i]
    tier_label = IMPACT_LEVELS.get(i, f"Tier {i}")

    ax.plot(fpr, tpr, color=colors[i], lw=3, label=f'AUC = {roc_auc:0.2f}')
    ax.plot([0, 1], [0, 1], color='black', lw=1.5, linestyle='--', label='Random Guess')

    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel('False Positive Rate', fontsize=10)
    ax.set_ylabel('True Positive Rate', fontsize=10)
    ax.set_title(f'ROC: {tier_label}', fontsize=12, fontweight='bold')
    ax.legend(loc="lower right")
    ax.grid(True, linestyle=':', alpha=0.6)

# Remove the unused 6th subplot
fig.delaxes(axes[5])

plt.suptitle('Individual ROC Curves by Stroke Impact Tier', fontsize=18, fontweight='bold', y=0.98)
plt.tight_layout(rect=[0, 0.03, 1, 0.95])

# Save the high-res figure
output_file = os.path.join(SCRIPT_DIR, 'individual_tier_roc_curves.png')
plt.savefig(output_file, bbox_inches='tight')
print(f"✅ Success! Individual ROC curves saved to: {output_file}")
plt.show()