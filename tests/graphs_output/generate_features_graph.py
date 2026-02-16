import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# --- 1. DATA PREPARATION ---
# Data extracted from your provided model output logs
pattern_data = {
    'pattern_volatility': 18.425,
    'pattern_velocity_trend': 10.615,
    'pattern_consistency': 8.325,
    'pattern_amplitude': 7.138,
    'pattern_stuttering_score': 4.481,
    'pattern_asymmetry_progression': 0.159,
    'pattern_type': 0.000,
    'pattern_reading_count': 0.000
}

# Convert to DataFrame and clean up names for display
df_p = pd.DataFrame(list(pattern_data.items()), columns=['Feature', 'Raw_Importance'])
df_p['Display_Name'] = df_p['Feature'].str.replace('pattern_', '').str.replace('_', ' ').str.title()

# Calculate Relative Weight (Contribution within the pattern group only)
total_pattern_weight = df_p['Raw_Importance'].sum()
df_p['Relative_Weight'] = (df_p['Raw_Importance'] / total_pattern_weight) * 100

# Sort for the graph
df_p = df_p.sort_values('Relative_Weight', ascending=True)

# --- 2. VISUALIZATION ---
plt.figure(figsize=(10, 6), dpi=300)

# Creating the horizontal bar chart
bars = plt.barh(df_p['Display_Name'], df_p['Relative_Weight'],
                color=plt.cm.Blues(np.linspace(0.4, 0.8, len(df_p))),
                edgecolor='black', alpha=0.9)

# Add value labels to the end of each bar
for bar in bars:
    width = bar.get_width()
    plt.text(width + 1, bar.get_y() + bar.get_height()/2,
             f'{width:.1f}%', va='center', fontweight='bold', fontsize=10)

# Formatting the Chart
plt.title('Subanalysis: Impact of Temporal Dynamic Features', fontsize=14, fontweight='bold', pad=20)
plt.xlabel('Relative Contribution to Pattern Intelligence (%)', fontsize=11, fontweight='bold')
plt.xlim(0, 55) # Leave space for the labels
plt.grid(axis='x', linestyle='--', alpha=0.4)

# Aesthetics
plt.gca().spines['top'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.tight_layout()

# Save the output
save_path = 'pattern_importance_subanalysis.png'
plt.savefig(save_path)
print(f"✅ Visualization saved to: {save_path}")
plt.show()