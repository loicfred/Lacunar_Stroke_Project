import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime

# ============================================
# PATH CONFIGURATION
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Updated paths based on your environment
possible_paths = [
    os.path.join(PROJECT_ROOT, "src", "data_simulation", "master_data", "stroke_training_data.csv"),
    os.path.join(PROJECT_ROOT, "data_simulation", "master_data", "stroke_training_data.csv"),
    os.path.join(BASE_DIR, "stroke_training_data.csv"),
    "stroke_training_data.csv"
]

DATA_PATH = None
for path in possible_paths:
    if os.path.exists(path):
        DATA_PATH = path
        break

if DATA_PATH is None:
    raise FileNotFoundError(f"Could not find 'stroke_training_data.csv'. Please check the file location.")

OUTPUT_DIR = os.path.join(BASE_DIR, 'graphs_output')
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def generate_impact_tier_graphs():
    # Load dataset
    print(f"📖 Loading dataset from: {DATA_PATH}")
    df = pd.read_csv(DATA_PATH)

    impact_levels = {
        0: "Strong Response",
        1: "Slightly Reduced",
        2: "Moderately Reduced",
        3: "Significantly Reduced",
        4: "Weak Global Response"
    }

    # Prepare HTML content
    # Note: Emojis are used here, so we MUST save with utf-8 encoding
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Impact Tier Test Cases</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f0f2f5; color: #333; }}
            .container {{ max-width: 1000px; margin: auto; }}
            .graph-container {{ background: white; padding: 25px; margin-bottom: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            img {{ width: 100%; border-radius: 4px; border: 1px solid #eee; }}
            h1 {{ color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; }}
            h2 {{ color: #2c3e50; margin-top: 0; }}
            .metadata {{ background: #f8f9fa; padding: 10px; border-left: 4px solid #1a73e8; font-size: 0.9em; margin-bottom: 15px; }}
            .footer {{ text-align: center; margin-top: 40px; color: #777; font-size: 0.8em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Impact Tier Test Cases (Reference Graphs)</h1>
            <p>These graphs are generated using representative samples from the training dataset.</p>
            <p><strong>Generated on:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    """

    # Generate a graph for each impact tier
    for tier, label in impact_levels.items():
        # Get data for this tier
        tier_data = df[df['impact_tier'] == tier]

        if tier_data.empty:
            print(f"⚠️ No data for Tier {tier}, skipping...")
            continue

        # Get the first sample from the dataset for this tier
        sample = tier_data.iloc[0]

        plt.figure(figsize=(10, 5))

        # Simulation logic: use 5 points ending at the dataset's recorded score
        readings = np.arange(1, 6)
        left_val = sample['left_sensory_score']
        right_val = sample['right_sensory_score']
        volatility = sample['volatility_index']

        # Create a trend with slight randomness based on volatility
        # But ensure the last point (index 4) is exactly the dataset value
        left_trend = [left_val + (np.random.uniform(-1, 1) * volatility) for _ in range(4)] + [left_val]
        right_trend = [right_val + (np.random.uniform(-1, 1) * volatility) for _ in range(4)] + [right_val]

        plt.plot(readings, left_trend, color='#1a73e8', marker='o', label=f'Left Sensory (Final: {left_val})', linewidth=2)
        plt.plot(readings, right_trend, color='#d93025', marker='s', label=f'Right Sensory (Final: {right_val})', linewidth=2)

        plt.title(f"Impact Tier {tier}: {label}", fontsize=14, fontweight='bold')
        plt.xlabel("Test Sequence")
        plt.ylabel("Sensory Score (0-10)")
        plt.ylim(0, 11)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.legend()

        # Save the image
        filename = f"tier_{tier}_graph.png"
        plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=100)
        plt.close()

        # Add to HTML
        html_content += f"""
            <div class="graph-container">
                <h2>{label} (Tier {tier})</h2>
                <div class="metadata">
                    <strong>Patient ID:</strong> {sample['patient_id']} | 
                    <strong>Volatility:</strong> {volatility:.4f} | 
                    <strong>Pattern:</strong> {sample.get('pattern_type', 'N/A')}
                </div>
                <img src="{filename}" alt="Tier {tier} Visualization">
            </div>
        """
        print(f"✅ Generated graph for Tier {tier}")

    html_content += """
            <div class="footer">Lacunar Stroke Project - Automated Test Case Generator</div>
        </div>
    </body>
    </html>
    """

    # Save the HTML file with UTF-8 encoding to prevent UnicodeEncodeError
    output_html_path = os.path.join(OUTPUT_DIR, 'index.html')
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"\n✨ Success! All files saved in: {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_impact_tier_graphs()