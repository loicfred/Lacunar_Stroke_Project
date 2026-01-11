"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""

from flask import Flask, render_template, jsonify, request
import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))  # src/web/
parent_dir = os.path.dirname(current_dir)  # src/
sys.path.insert(0, parent_dir)

import data_simulation.patient_generator as patient_gen

import random
import datetime

app = Flask(__name__)

# ========== BLUE'S SECTION: DATA & MODELS ==========
def get_sample_patients():
    base_patients = patient_gen.generate_batch_patients(50)

    enhanced_patients = []
    for patient in base_patients:
        left_score = round(random.uniform(3.0, 10.0), 2)
        right_score = round(random.uniform(3.0, 10.0), 2)

        asymmetry = abs(left_score - right_score) > 2.0

        if asymmetry:
            affected_side = "Left" if left_score < right_score else "Right"
        else:
            affected_side = "None"

        enhanced_patient = {
            **patient,
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
    """
    left_score = patient_data.get("left_sensory_score", 5.0)
    right_score = patient_data.get("right_sensory_score", 5.0)

    asymmetry_detected = abs(left_score - right_score) > 2.0

    # Calculate confidence based on score difference
    score_diff = abs(left_score - right_score)
    confidence = min(0.95, 0.5 + (score_diff / 10))

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
        "model_used": "asymmetry_threshold"
    }

# ========== PURPLE'S SECTION: DASHBOARD ==========
def get_dashboard_stats():
    """
    PURPLE: Replace with real dashboard calculations
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
@app.route('/')
def home():
    """Main dashboard page"""
    stats = get_dashboard_stats()
    patients = get_sample_patients()[:5]  # First 5 only for display
    return render_template('index.html', stats=stats, patients=patients)

@app.route('/api/patients', methods=['GET'])
def api_get_patients():
    """API to get patient data"""
    patients = get_sample_patients()
    return jsonify({
        "success": True,
        "count": len(patients),
        "patients": patients[:20]  # Limit response size
    })

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """
    Main prediction endpoint
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
    """Dashboard data API"""
    stats = get_dashboard_stats()
    return jsonify({
        "success": True,
        "dashboard": stats
    })

# ========== GREEN'S SECTION: APP CONFIG ==========
@app.route('/status')
def status():
    """System status check"""
    return jsonify({
        "status": "operational",
        "components": {
            "flask_app": "running",
            "data_module": "connected",
            "prediction_module": "asymmetry_threshold",
            "dashboard_module": "basic_stats"
        },
        "message": "Green: Flask is running."
    })

@app.route('/test-data')
def test_data():
    """
    Test endpoint showing data
    """
    patients = get_sample_patients()
    total = len(patients)
    asymmetric = sum(1 for p in patients if p.get("asymmetry_label") == 1)

    return jsonify({
        "status": "connected",
        "data_source": "Blue's Patient Generator",
        "patient_count": total,
        "asymmetric_cases": asymmetric,
        "percentage_asymmetric": f"{(asymmetric/total*100):.1f}%",
        "sample_patients": patients[:3]
    })

@app.route('/api/generate-new/<int:count>')
def generate_new_patients(count):
    """
    GREEN: Endpoint to generate fresh patient data
    """
    if count > 100:
        return jsonify({
            "success": False,
            "error": "Maximum 100 patients allowed"
        }), 400


    new_patients = patient_gen.generate_batch_patients(count)
    data_source = "patient_generator.py"

    # Add stroke data to each patient
    enhanced_patients = []
    for patient in new_patients:
        left_score = round(random.uniform(3.0, 10.0), 2)
        right_score = round(random.uniform(3.0, 10.0), 2)
        asymmetry = abs(left_score - right_score) > 2.0

        enhanced_patient = {
            **patient,
            "left_sensory_score": left_score,
            "right_sensory_score": right_score,
            "affected_side": "Left" if left_score < right_score else "Right" if asymmetry else "None",
            "asymmetry_label": 1 if asymmetry else 0
        }
        enhanced_patients.append(enhanced_patient)

    return jsonify({
        "success": True,
        "message": f"Generated {count} new patients",
        "data_source": data_source,
        "patient_count": len(enhanced_patients),
        "patients": enhanced_patients[:5]
    })

# ========== ERROR HANDLING ==========
@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(_):
    return jsonify({"success": False, "error": "Internal server error"}), 500

# ========== MAIN EXECUTION ==========
if __name__ == '__main__':
    print("=" * 50)
    print("LACUNAR STROKE DETECTION SYSTEM")
    print("=" * 50)

    print("\n📊 Test endpoints:")
    print("   http://localhost:5000/              - Dashboard")
    print("   http://localhost:5000/status        - System status")
    print("   http://localhost:5000/test-data     - Check Blue's data")
    print("   http://localhost:5000/api/patients  - Get all patients")
    print("   http://localhost:5000/api/generate-new/10 - Generate new patients")
    print("=" * 50)

    app.run(host="0.0.0.0", debug=True, port=5000)