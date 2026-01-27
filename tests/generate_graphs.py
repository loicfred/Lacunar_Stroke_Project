import matplotlib.pyplot as plt
import numpy as np
import os
from datetime import datetime  # ADD THIS LINE

# Create the tests directory if it doesn't exist
current_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(current_dir, 'graphs_output')

if not os.path.exists(output_dir):
    os.makedirs(output_dir)
    print(f"📁 Created directory: {output_dir}")

print("📊 Generating accurate graphs based on your code logic...")

# ============================================
# GRAPH 1: BASELINE ESTABLISHMENT (Diya)
# ============================================
plt.figure(figsize=(12, 6))

days = np.arange(1, 8)

# Simulate sensory scores based on YOUR code (0-10 scale)
left_scores = [8.5, 8.3, 8.7, 8.4, 8.6, 8.5, 8.6]
right_scores = [8.7, 8.6, 8.5, 8.8, 8.5, 8.6, 8.5]

# Normal range from your code (strong response)
normal_min = 7.5  # Based on your threshold logic
normal_max = 10.0

plt.plot(days, left_scores, 'b-o', linewidth=2, label='Left Hand', markersize=8)
plt.plot(days, right_scores, 'r-s', linewidth=2, label='Right Hand', markersize=8)

# Fill normal range (from your asymmetry thresholds)
plt.fill_between(days, normal_min, normal_max, alpha=0.1, color='green', label='Normal Range (7.5-10.0)')

# Your system's decision points
plt.axhline(y=7.5, color='orange', linestyle='--', alpha=0.7, linewidth=1.5, label='Warning Threshold (7.5)')
plt.axhline(y=6.0, color='red', linestyle='--', alpha=0.7, linewidth=1.5, label='Alert Threshold (6.0)')

plt.xlabel('Days (1-7)', fontsize=12)
plt.ylabel('Sensory Score (0-10 scale)', fontsize=12)
plt.title('GRAPH 1: BASELINE ESTABLISHMENT', fontsize=14, fontweight='bold')
plt.legend(loc='lower right')
plt.grid(True, alpha=0.3)
plt.ylim(5, 10)
plt.xlim(0.5, 7.5)

# Add asymmetry index on secondary axis (as in your code)
ax2 = plt.gca().twinx()
asymmetry = np.abs(np.array(left_scores) - np.array(right_scores)) / (np.array(left_scores) + np.array(right_scores)) * 100
ax2.plot(days, asymmetry, 'g--', linewidth=1.5, alpha=0.5, label='Asymmetry Index')
ax2.set_ylabel('Asymmetry Index (%)', fontsize=12, color='green')
ax2.set_ylim(0, 20)
ax2.axhline(y=10, color='orange', linestyle=':', alpha=0.5, linewidth=1)
ax2.axhline(y=15, color='red', linestyle=':', alpha=0.5, linewidth=1)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'graph1_baseline.png'), dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Graph 1 saved: {os.path.join(output_dir, 'graph1_baseline.png')}")

# ============================================
# GRAPH 2: STROKE DETECTION TIMELINE (Loic)
# ============================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True, gridspec_kw={'height_ratios': [2, 1]})

# Simulate 24-hour timeline based on YOUR test case logic
hours = np.arange(0, 24, 0.5)  # 48 points over 24 hours

# Initial scores (from your code's baseline)
left_baseline = 8.5 + np.random.normal(0, 0.2, len(hours))
right_baseline = 8.7 + np.random.normal(0, 0.2, len(hours))

# Introduce stroke at hour 12 (as in your test case)
stroke_hour = 12
for i in range(len(hours)):
    if hours[i] >= stroke_hour:
        # Gradual decline with stuttering (as in your code)
        progression = (hours[i] - stroke_hour) * 0.08  # Slower progression for 0-10 scale

        # Add stuttering pattern (sudden drops and partial recoveries)
        if i % 6 == 0:  # Stuttering every ~3 hours
            right_baseline[i] -= np.random.uniform(0.3, 0.8)
        else:
            right_baseline[i] -= progression

        # Add noise
        right_baseline[i] += np.random.normal(0, 0.1)

# Plot left and right scores
ax1.plot(hours, left_baseline, 'b-', linewidth=2, label='Left Hand', alpha=0.8)
ax1.plot(hours, right_baseline, 'r-', linewidth=2, label='Right Hand', alpha=0.8)

# Mark stroke onset
ax1.axvline(x=stroke_hour, color='red', linestyle='--', alpha=0.5, label='Stroke Onset')
ax1.fill_between([stroke_hour, 24], 0, 10, alpha=0.1, color='red')

# Your system's thresholds
ax1.axhline(y=7.5, color='orange', linestyle='--', alpha=0.5, linewidth=1)
ax1.axhline(y=6.0, color='red', linestyle='--', alpha=0.5, linewidth=1)

ax1.set_ylabel('Sensory Score (0-10 scale)', fontsize=12)
ax1.set_title('GRAPH 2: STROKE DETECTION TIMELINE', fontsize=14, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_ylim(4, 10)

# Plot asymmetry index (as calculated in your code)
asymmetry_index = np.abs(left_baseline - right_baseline) / ((left_baseline + right_baseline) / 2 + 1e-10) * 100
ax2.plot(hours, asymmetry_index, 'g-', linewidth=2, alpha=0.8)

# Your asymmetry thresholds from code
ax2.axhline(y=10, color='yellow', linestyle='--', alpha=0.7, label='Yellow Alert (10%)')
ax2.axhline(y=20, color='red', linestyle='--', alpha=0.7, label='Red Alert (20%)')
ax2.axhline(y=5, color='gray', linestyle=':', alpha=0.5, label='Normal Range (<5%)')

# Mark when asymmetry crosses thresholds
cross_10_idx = np.where(asymmetry_index > 10)[0]
cross_20_idx = np.where(asymmetry_index > 20)[0]

if len(cross_10_idx) > 0:
    ax2.axvline(x=hours[cross_10_idx[0]], color='yellow', linestyle=':', alpha=0.3)
    ax2.annotate('Asymmetry >10%', (hours[cross_10_idx[0]], 12),
                 xytext=(10, 0), textcoords='offset points',
                 ha='left', fontsize=8, color='yellow')

if len(cross_20_idx) > 0:
    ax2.axvline(x=hours[cross_20_idx[0]], color='red', linestyle=':', alpha=0.3)
    ax2.annotate('Asymmetry >20%', (hours[cross_20_idx[0]], 22),
                 xytext=(10, 0), textcoords='offset points',
                 ha='left', fontsize=8, color='red')

ax2.set_xlabel('Hours (0-24)', fontsize=12)
ax2.set_ylabel('Asymmetry Index (%)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 40)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'graph2_stroke_timeline.png'), dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Graph 2 saved: {os.path.join(output_dir, 'graph2_stroke_timeline.png')}")

# ============================================
# GRAPH 3: STUTTERING PATTERN ANALYSIS (Corrected)
# ============================================
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), gridspec_kw={'height_ratios': [2, 1]})

# Simulate 30 days of monitoring (0-10 scale)
np.random.seed(42)
days = np.arange(1, 31)

# Base trend: healthy patient with slight decline
base_scores = 8.5 - (days * 0.01)  # Very slow decline

# Add stuttering pattern (as detected by your volatility_index function)
stuttering_pattern = base_scores.copy()

# Add sudden drops and partial recoveries (lacunar stroke pattern)
stutter_days = [5, 8, 12, 15, 20, 23, 27]
for day in stutter_days:
    idx = day - 1  # Convert to 0-index
    if idx < len(stuttering_pattern):
        # Sudden drop (0.5-1.5 points, consistent with your 0-10 scale)
        drop = np.random.uniform(0.5, 1.5)
        stuttering_pattern[idx] -= drop

        # Partial recovery next day (0.2-0.8 points)
        if idx + 1 < len(stuttering_pattern):
            recovery = np.random.uniform(0.2, 0.8)
            stuttering_pattern[idx + 1] += recovery

# Add biological noise (as in your Gaussian distributions)
stuttering_pattern += np.random.normal(0, 0.15, len(days))

# Clip to valid range
stuttering_pattern = np.clip(stuttering_pattern, 0, 10)

# Plot sensory scores
ax1.plot(days, stuttering_pattern, 'b-', linewidth=2, label='Affected Hand (Right)', alpha=0.8)
ax1.scatter(days, stuttering_pattern, c='blue', s=30, alpha=0.7)

# Highlight stuttering events
for day in stutter_days:
    idx = day - 1
    if idx < len(days):
        ax1.axvspan(day, day+0.5, alpha=0.2, color='red')
        ax1.annotate('Stutter', (day, stuttering_pattern[idx]),
                     xytext=(0, 15), textcoords='offset points',
                     ha='center', fontsize=8, color='red')

# Add unaffected hand for comparison (stable)
unaffected = 8.5 + np.random.normal(0, 0.1, len(days))
ax1.plot(days, unaffected, 'g--', linewidth=2, label='Unaffected Hand (Left)', alpha=0.6)

# Your system thresholds
ax1.axhline(y=7.5, color='orange', linestyle='--', alpha=0.5, label='Warning (7.5)')
ax1.axhline(y=6.0, color='red', linestyle='--', alpha=0.5, label='Alert (6.0)')

ax1.set_xlabel('Days of Monitoring', fontsize=12)
ax1.set_ylabel('Sensory Score (0-10 scale)', fontsize=12)
ax1.set_title('GRAPH 3: STUTTERING PATTERN DETECTION', fontsize=14, fontweight='bold')
ax1.legend(loc='upper right')
ax1.grid(True, alpha=0.3)
ax1.set_xlim(1, 30)
ax1.set_ylim(4, 10)

# Calculate volatility index EXACTLY as your code does
def calculate_volatility_scores(scores, window=5):
    """Replicate your calculate_volatility_index function"""
    volatility = np.zeros(len(scores))
    for i in range(len(scores)):
        if i >= window:
            window_scores = scores[i-window:i+1]
            volatility[i] = np.std(window_scores)  # YOUR formula: np.std(scores)
    return volatility

volatility = calculate_volatility_scores(stuttering_pattern)

# Plot volatility
ax2.plot(days, volatility, 'g-', linewidth=2)
ax2.fill_between(days, 0, volatility, alpha=0.3, color='green')

# Your volatility thresholds (from your code patterns)
ax2.axhline(y=0.3, color='orange', linestyle='--', label='Warning (0.3)')
ax2.axhline(y=0.5, color='red', linestyle='--', label='Alert (0.5)')

# Mark high volatility periods
high_vol = np.where(volatility > 0.4)[0]
for idx in high_vol:
    ax2.annotate('High Volatility', (days[idx], volatility[idx]),
                 xytext=(0, 10), textcoords='offset points',
                 ha='center', fontsize=8, color='red', fontweight='bold')

ax2.set_xlabel('Days', fontsize=12)
ax2.set_ylabel('Volatility Index (Std Dev)', fontsize=12)
ax2.set_title('Pattern Volatility (as calculated by calculate_volatility_index)', fontsize=12)
ax2.legend(loc='upper right')
ax2.grid(True, alpha=0.3)
ax2.set_xlim(1, 30)
ax2.set_ylim(0, 1.0)

plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'graph3_stuttering_corrected.png'), dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Graph 3 saved: {os.path.join(output_dir, 'graph3_stuttering_corrected.png')}")

# ============================================
# TEST CASES (Based on your patient_generator.py logic)
# ============================================
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Create test cases based on YOUR actual logic
time_points = np.arange(0, 24, 1)  # Hourly readings for 24 hours

# Case A: Stroke Detection (from your test case narrative)
def case_a_stroke():
    # Healthy baseline (8.5-8.7 range)
    left = 8.5 + np.random.normal(0, 0.1, len(time_points))
    right = 8.7 + np.random.normal(0, 0.1, len(time_points))

    # Stroke starts at hour 12
    stroke_hour = 12
    for i in range(len(time_points)):
        if time_points[i] >= stroke_hour:
            # Gradual decline with stuttering
            decline_rate = 0.1  # points per hour
            right[i] -= decline_rate * (time_points[i] - stroke_hour)

            # Add stuttering (sudden drops)
            if (time_points[i] - stroke_hour) % 3 == 0:
                right[i] -= np.random.uniform(0.3, 0.8)

    # Add noise
    left += np.random.normal(0, 0.05, len(left))
    right += np.random.normal(0, 0.05, len(right))

    return np.clip(left, 0, 10), np.clip(right, 0, 10)

# Case B: Medication Effect (from Ms. Chen case)
def case_b_medication():
    # Lower baseline due to neuropathy (6.5-7.0 range)
    left = 6.5 + np.random.normal(0, 0.3, len(time_points))
    right = 6.5 + np.random.normal(0, 0.3, len(time_points))

    # Medication at hour 8 improves right hand
    med_hour = 8
    for i in range(len(time_points)):
        if time_points[i] >= med_hour:
            improvement = 0.05 * (time_points[i] - med_hour)
            right[i] += min(improvement, 1.0)  # Max 1 point improvement

    return np.clip(left, 0, 10), np.clip(right, 0, 10)

# Case C: Measurement Error (as in your code)
def case_c_error():
    # Normal scores
    left = 8.5 + np.random.normal(0, 0.1, len(time_points))
    right = 8.7 + np.random.normal(0, 0.1, len(time_points))

    # Error at hour 6 (dropped device)
    error_hour = 6
    error_idx = np.argmin(np.abs(time_points - error_hour))
    right[error_idx] = 2.0  # Very low score

    # Quick recovery (retest)
    right[error_idx + 1] = 8.5
    right[error_idx + 2] = 8.6

    return np.clip(left, 0, 10), np.clip(right, 0, 10)

# Case D: Normal Baseline
def case_d_normal():
    left = 8.5 + np.random.normal(0, 0.15, len(time_points))
    right = 8.7 + np.random.normal(0, 0.15, len(time_points))
    return np.clip(left, 0, 10), np.clip(right, 0, 10)

# Plot all cases
cases = [
    ("A: Stroke Detection", case_a_stroke(), 'red'),
    ("B: Medication Effect", case_b_medication(), 'orange'),
    ("C: Measurement Error", case_c_error(), 'blue'),
    ("D: Normal Baseline", case_d_normal(), 'green')
]

for idx, (title, (left, right), color) in enumerate(cases):
    ax = axes[idx // 2, idx % 2]

    ax.plot(time_points, left, 'b-', linewidth=2, label='Left Hand', alpha=0.7)
    ax.plot(time_points, right, 'r-', linewidth=2, label='Right Hand', alpha=0.7)

    # Add your system's thresholds
    ax.axhline(y=7.5, color='orange', linestyle='--', alpha=0.3, linewidth=1)
    ax.axhline(y=6.0, color='red', linestyle='--', alpha=0.3, linewidth=1)

    # Mark key events
    if idx == 0:  # Stroke case
        ax.axvspan(12, 24, alpha=0.1, color='red')
        ax.annotate('Stroke\nOnset', (12, right[12]),
                    xytext=(10, -20), textcoords='offset points',
                    ha='center', fontsize=9, color='red')
    elif idx == 1:  # Medication
        ax.axvline(x=8, color='orange', linestyle='--', alpha=0.7)
        ax.annotate('Medication', (8, 7),
                    xytext=(0, 20), textcoords='offset points',
                    ha='center', fontsize=9, color='orange')
    elif idx == 2:  # Error
        ax.scatter(6, right[6], s=200, color='red', marker='X', zorder=5)
        ax.annotate('Measurement\nError', (6, right[6]),
                    xytext=(0, 30), textcoords='offset points',
                    ha='center', fontsize=9, color='red')

    ax.set_xlabel('Hours', fontsize=10)
    ax.set_ylabel('Sensory Score', fontsize=10)
    ax.set_title(title, fontsize=12, fontweight='bold', color=color)
    ax.legend(loc='best', fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 10)
    ax.set_xlim(0, 23)

plt.suptitle('TEST CASES: SYSTEM BEHAVIOR UNDER DIFFERENT SCENARIOS',
             fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(output_dir, 'test_cases_corrected.png'), dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Test Cases saved: {os.path.join(output_dir, 'test_cases_corrected.png')}")

print(f"\n📁 All graphs saved in '{output_dir}' folder!")
print("📍 Location:", os.path.abspath(output_dir))

# Create a simple HTML viewer
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Stroke Detection System Graphs</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #2c3e50; }}
        .graph {{ margin: 20px 0; border: 1px solid #ddd; padding: 10px; }}
        .graph img {{ max-width: 100%; height: auto; }}
        .caption {{ color: #666; font-size: 14px; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>📊 Stroke Detection System Graphs</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="graph">
        <h2>Graph 1: Baseline Establishment</h2>
        <img src="graph1_baseline.png" alt="Baseline Graph">
        <div class="caption">Shows first 7 days establishing normal range with 0-10 scale sensory scores</div>
    </div>
    
    <div class="graph">
        <h2>Graph 2: Stroke Detection Timeline</h2>
        <img src="graph2_stroke_timeline.png" alt="Stroke Timeline Graph">
        <div class="caption">24-hour period showing stroke onset with stuttering pattern</div>
    </div>
    
    <div class="graph">
        <h2>Graph 3: Stuttering Pattern Analysis</h2>
        <img src="graph3_stuttering_corrected.png" alt="Stuttering Pattern Graph">
        <div class="caption">30-day monitoring showing lacunar stroke stuttering pattern with volatility index</div>
    </div>
    
    <div class="graph">
        <h2>Test Cases Comparison</h2>
        <img src="test_cases_corrected.png" alt="Test Cases Graph">
        <div class="caption">Four scenarios showing system behavior with different conditions</div>
    </div>
</body>
</html>
"""

# Save HTML viewer
html_path = os.path.join(output_dir, 'index.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"📄 HTML viewer created: {html_path}")
print(f"📂 Open this file in your browser to view all graphs: file://{os.path.abspath(html_path)}")