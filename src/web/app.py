"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""

from flask import Flask, render_template, jsonify, request
import data_simulation.patient_generator as patient_gen
import random
import sys
import os

from model.Patient import Patient
from model.SensoryDetails import SensoryDetails

current_dir = os.path.dirname(os.path.abspath(__file__))  # src/web/
parent_dir = os.path.dirname(current_dir)  # src/
sys.path.insert(0, parent_dir)


app = Flask(__name__)


# ========== CONTROLLER API ==========


sample_patient_list = []

def get_sample_patients():
    global sample_patient_list
    if not sample_patient_list: sample_patient_list = add_sample_patients(5)
    return sample_patient_list
@app.route('/api/patients', methods=['GET'])  # To get all sample patients
def api_get_sample_patients():
    patients = get_sample_patients()
    return jsonify({
        "success": True,
        "count": len(patients),
        "patients": patients  # Limit response size
    })


def clear_sample_patients():
    global sample_patient_list
    sample_patient_list = []
@app.route('/api/clear', methods=["GET"]) # To generate new fresh patient data.
def api_clear_sample_patients():
    clear_sample_patients()
    return jsonify({
        "success": True,
        "message": "Cleared sample patients"
    })


def add_sample_patients(amount: int = 1):
    global sample_patient_list
    samplePatients = []
    for patient in patient_gen.generate_batch_patient_details(amount):
        left_score = round(random.uniform(3.0, 10.0), 2)
        right_score = round(random.uniform(3.0, 10.0), 2)
        asymmetry = abs(left_score - right_score) > 2.0
        if asymmetry:
            affected_side = "Left" if left_score < right_score else "Right"
        else:
            affected_side = "None"
        asymmetry_label = 1 if asymmetry else 0
        sensory_details = SensoryDetails(left_score, right_score, affected_side, asymmetry_label)

        samplePatients.append(Patient.create(patient, sensory_details))
        sample_patient_list.append(samplePatients)
    return samplePatients
@app.route('/api/generate-new/<int:count>', methods=["GET"]) # To generate new fresh patient data.
def api_add_sample_patients(amount):
    if amount > 100:
        return jsonify({
            "success": False,
            "error": "Maximum 100 patients allowed"
        }), 400
    else:
        new_patients = add_sample_patients(amount)
        data_source = "patient_generator.py"
        return jsonify({
            "success": True,
            "message": f"Generated {amount} new patients",
            "data_source": data_source,
            "new_patient_count": len(new_patients),
            "new_patients": new_patients
        })


def predict_stroke(patient_data):
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
@app.route('/api/predict', methods=['POST']) # Send patient's data to return a prediction.
def api_predict_stroke():
    try:
        patient_data = request.json # Get request body as JSON
        if not patient_data:
            return jsonify({
                "success": False, "error": "No patient data provided"
            }), 400

        prediction = predict_stroke(patient_data)  # Get prediction from model
        return jsonify({
            "success": True, "prediction": prediction, "received_data": patient_data
        })
    except Exception as e: return jsonify({"success": False, "error": str(e)}), 500

def get_dashboard_stats():
    patients = get_sample_patients()
    total = len(patients)
    asymmetric = sum(1 for p in patients if p.get("asymmetry_label") == 1)
    return {
        "total_patients": total,
        "asymmetric_cases": asymmetric,
        "asymmetric_percentage": (asymmetric/total*100) if total > 0 else 0,
        "avg_left_score": sum(p.left_sensory_score for p in patients)/total if total > 0 else 0,
        "avg_right_score": sum(p.right_sensory_score for p in patients)/total if total > 0 else 0
    }
@app.route('/api/dashboard', methods=['GET'])
def api_get_dashboard_stats(): # The statistics of the dashboard. eg. percentages
    return jsonify({"success": True, "dashboard": get_dashboard_stats()})


# ========== CONTROLLER PAGE ==========


@app.route('/')
def home():
    stats = get_dashboard_stats()
    patients = get_sample_patients()[:5]  # First 5 only for display
    return render_template('index.html', stats=stats, patients=patients)


# ========== MISC CONTROLLER ==========


@app.route('/status')  # To check system status (fake)
def status():
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


# ========== ERROR CONTROLLER ==========


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