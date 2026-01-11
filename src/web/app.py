"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""

from flask import Flask, render_template, jsonify, request
import json
# GREEN: Add these imports to connect with Blue's work
import patient_generator
import random  # For generating sensory scores

from data_simulation.patient_generator import generate_patients

app = Flask(__name__)

# ========== BLUE'S SECTION: DATA & MODELS ==========
# Blue will implement these functions - NOW CONNECTED!
def get_sample_patients(generate_patients=None):
    """
    GREEN: Now connected to Blue's patient_generator.py
    Generates 50 patients with realistic stroke data
    """
    # Use Blue's function to generate patients
    base_patients = generate_patients(50)

    enhanced_patients = []
    for patient in base_patients:
        # Add stroke-specific data (simulated for now)
        left_score = round(random.uniform(3.0, 10.0), 2)
        right_score = round(random.uniform(3.0, 10.0), 2)

        # Determine asymmetry (difference > 2.0 indicates potential stroke)
        asymmetry = abs(left_score - right_score) > 2.0

        # Determine affected side
        if asymmetry:
            affected_side = "Left" if left_score < right_score else "Right"
        else:
            affected_side = "None"

        enhanced_patient = {
            **patient,  # Keep all Blue's data
            "left_sensory_score": left_score,
            "right_sensory_score": right_score,
            "affected_side": affected_side,
            "asymmetry_label": 1 if asymmetry else 0
        }
        enhanced_patients.append(enhanced_patient)

    return enhanced_patients

def predict_stroke(patient_data):
    """
    GREEN/BLUE: Enhanced prediction with real patient data
    Uses the asymmetry logic from above
    """
    left_score = patient_data.get("left_sensory_score", 5.0)
    right_score = patient_data.get("right_sensory_score", 5.0)

    asymmetry_detected = abs(left_score - right_score) > 2.0

    # Calculate confidence based on score difference
    score_diff = abs(left_score - right_score)
    confidence = min(0.95, 0.5 + (score_diff / 10))  # Scale to 0.5-0.95

    # Determine risk level
    if asymmetry_detected:
        risk_level = "high"
        affected_side = "Left" if left_score < right_score else "Right"
    else:
        risk_level = "low"
        affected_side = "None"

    return {
        "asymmetry_detected": asymmetry_detected,
        "confidence": round(confidence, 2),
        "risk_level": risk_level,
        "affected_side": affected_side,
        "score_difference": round(score_diff, 2),
        "model_used": "asymmetry_threshold"  # Will be replaced with real ML model
    }

# ========== PURPLE'S SECTION: DASHBOARD ==========
# Purple will implement these visualizations
def get_dashboard_stats():
    """
    PURPLE: Replace with real dashboard calculations
    Returns basic statistics for the dashboard.
    """
    patients = get_sample_patients()
    total = len(patients)
    asymmetric = sum(1 for p in patients if p.get("asymmetry_label") == 1)

    return {
        "total_patients": total,
        "asymmetric_cases": asymmetric,
        "asymmetric_percentage": (asymmetric/total*100) if total > 0 else 0,
        "avg_left_score": sum(p.get("left_sensory_score", 0) for p in patients)/total if total > 0 else 0,
        "avg_right_score": sum(p.get("right_sensory_score", 0) for p in patients)/total if total > 0 else 0
    }

# ========== RED'S SECTION: API ENDPOINTS ==========
# Red will enhance these endpoints

@app.route('/')
def home():
    """Main dashboard page - Purple will style this"""
    stats = get_dashboard_stats()
    patients = get_sample_patients()
    return render_template('index.html', stats=stats, patients=patients)

@app.route('/api/patients', methods=['GET'])
def api_get_patients():
    """API to get patient data - Blue provides real data here"""
    patients = get_sample_patients()
    return jsonify({
        "success": True,
        "count": len(patients),
        "patients": patients
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    RED/BLUE: Main prediction endpoint
    Blue provides model, Red handles API logic
    """
    try:
        # Get data from request
        patient_data = request.json

        if not patient_data:
            return jsonify({
                "success": False,
                "error": "No patient data provided"
            }), 400

        # Get prediction from model
        prediction = predict_stroke(patient_data)

        return jsonify({
            "success": True,
            "prediction": prediction,
            "received_data": patient_data
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/dashboard', methods=['GET'])
def api_dashboard():
    """Dashboard data API - Purple enhances this"""
    stats = get_dashboard_stats()
    return jsonify({
        "success": True,
        "dashboard": stats
    })

# ========== GREEN'S SECTION: APP CONFIG ==========
# Green handles all Flask setup and configuration

@app.route('/status')
def status():
    """System status check - All members should ensure their parts work"""
    return jsonify({
        "status": "operational",
        "components": {
            "flask_app": "running",
            "data_module": "mock_data" if len(get_sample_patients()) > 0 else "not_implemented",
            "prediction_module": "mock_predictions",
            "dashboard_module": "basic_stats"
        },
        "message": "Green: Flask is running. Other members: implement your sections above."
    })

@app.route('/test-data')
def test_data():
    """
    Test endpoint showing the data from screenshot
    Blue: Connect your real data generator here
    """
    return jsonify({
        "sample_data_from_screenshot": get_sample_patients(),
        "note": "Blue: Replace get_sample_patients() with real data generation"
    })

# ========== ERROR HANDLING ==========
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ========== MAIN EXECUTION ==========
if __name__ == '__main__':
    print("=" * 50)
    print("LACUNAR STROKE DETECTION SYSTEM")
    print("=" * 50)
    print("Green: Flask app starting on http://localhost:5000")
    print("\nTeam Integration Points:")
    print("1. BLUE: Implement get_sample_patients() with real data")
    print("2. BLUE/RED: Implement predict_stroke() with ML models")
    print("3. PURPLE: Enhance get_dashboard_stats() and templates")
    print("4. RED: Enhance API endpoints and error handling")
    print("=" * 50)

    app.run(host="0.0.0.0",debug=True, port=5000)