"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""

from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)

# ========== BLUE'S SECTION: DATA & MODELS ==========
# Blue will implement these functions
def get_sample_patients():
    """
    BLUE: Replace this with real data from patient_generator.py
    Currently returns example data from the screenshot.
    """
    return [
        {"patient_id": 1, "age_group": "60-69", "sex": "Male", "hypertension": 0, "diabetes": 1, "smoking_history": 1, "left_sensory_score": 5.6, "right_sensory_score": 8.39, "affected_side": "Left", "asymmetry_label": 1},
        {"patient_id": 2, "age_group": "80-89", "sex": "Male", "hypertension": 0, "diabetes": 1, "smoking_history": 0, "left_sensory_score": 9.18, "right_sensory_score": 9.21, "affected_side": "None", "asymmetry_label": 0}
    ]

def predict_stroke(patient_data):
    """
    BLUE/RED: Replace with actual ML model prediction
    Returns mock prediction for now.
    """
    return {
        "asymmetry_detected": patient_data.get("asymmetry_label", 0) == 1,
        "confidence": 0.85,
        "risk_level": "high" if patient_data.get("asymmetry_label", 0) == 1 else "low",
        "model_used": "random_forest"  # Blue: Change to actual model name
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

    app.run(debug=True, port=5000)