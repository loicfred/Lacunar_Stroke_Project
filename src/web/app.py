"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""
import logging;
import time

from model.PatientDetails import PatientDetails

logging.basicConfig(level=logging.INFO)

from flask import Flask, render_template, jsonify, request
import data_simulation.patient_generator as patient_gen
import random
import sys
import os
import joblib
import pandas as pd

from model.Patient import Patient
from model.SensoryDetails import SensoryDetails

current_dir = os.path.dirname(os.path.abspath(__file__))  # src/web/
parent_dir = os.path.dirname(current_dir)  # src/
sys.path.insert(0, parent_dir)


app = Flask(__name__)


# ========== LOAD STROKE MODEL ==========
print("=" * 50)
print("🤖 LOADING STROKE PREDICTION MODEL")
print("=" * 50)

# Get project root (go up from 'web/' to project root)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Go up TWO levels from src/web/app.py to reach project root
MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'stroke_model.pkl')

model = None
try:
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at: {MODEL_PATH}")

    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded successfully from: {MODEL_PATH}")
    print(f"📊 Model type: {type(model).__name__}")

    # Debug: Show model info
    if hasattr(model, 'feature_names_in_'):
        print(f"📋 Expected features: {list(model.feature_names_in_)}")
    if hasattr(model, 'classes_'):
        print(f"🎯 Model classes: {model.classes_}")

except Exception as e:
    print(f"❌ ERROR loading model: {e}")
    import traceback
    traceback.print_exc()
    print("⚠️ Continuing with threshold-based fallback...")

print("=" * 50)


# ========== SAMPLE DATA ==========
sample_patient_list = []


# ========== MODEL PREDICTION FUNCTION ==========
def predict_with_model(patient_data):
    """
    Use the trained ML model to predict stroke risk
    Returns: prediction result dictionary
    """
    if model is None:
        return None  # Indicate model not available

    try:
        # Extract features from patient data
        left_score = patient_data.get("left_sensory_score", 5.0)
        right_score = patient_data.get("right_sensory_score", 5.0)

        # Calculate asymmetry index
        avg = (left_score + right_score) / 2
        if avg > 0:
            asymmetry_index = abs(left_score - right_score) / avg
        else:
            asymmetry_index = 0

        # Prepare data for model
        input_data = pd.DataFrame([[left_score, right_score, asymmetry_index]],
                                  columns=['left_sensory_score',
                                           'right_sensory_score',
                                           'asymmetry_index'])

        # Make prediction
        prediction = model.predict(input_data)[0]

        # Get probabilities if available
        confidence = 0.85  # Default confidence
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(input_data)[0]
            confidence = max(probabilities)

        # Map prediction to readable labels
        risk_labels = {
            0: ("Normal", "low", "🟢"),
            1: ("Unilateral Risk", "medium", "🟡"),
            2: ("Bilateral Risk", "high", "🔴")
        }

        label, risk_level, emoji = risk_labels.get(prediction, ("Unknown", "unknown", "⚪"))

        # Determine affected side for unilateral cases
        affected_side = "None"
        if prediction == 1:  # Unilateral Risk
            affected_side = "Left" if left_score < right_score else "Right"

        return {
            "prediction_code": int(prediction),
            "prediction_label": label,
            "risk_level": risk_level,
            "emoji": emoji,
            "confidence": round(confidence, 3),
            "affected_side": affected_side,
            "asymmetry_index": round(asymmetry_index, 3),
            "model_used": "trained_ml_model",
            "model_type": type(model).__name__
        }

    except Exception as e:
        print(f"Model prediction error: {e}")
        return None


# ========== FALLBACK PREDICTION (Existing Logic) ==========
def predict_stroke_threshold(patient_data):
    """
    Fallback prediction using threshold logic
    """
    left_score = patient_data.get("left_sensory_score", 5.0)
    right_score = patient_data.get("right_sensory_score", 5.0)

    asymmetry_detected = abs(left_score - right_score) > 2.0

    # Calculate confidence based on score difference
    score_diff = abs(left_score - right_score)
    confidence = min(0.95, 0.5 + (score_diff / 10))

    # Determine risk level
    if asymmetry_detected:
        risk_level = "medium"  # Changed from "high" to differentiate from model
        affected_side = "Left" if left_score < right_score else "Right"
        label = "Asymmetry Detected"
    else:
        risk_level = "low"
        affected_side = "None"
        label = "Normal"

    return {
        "asymmetry_detected": asymmetry_detected,
        "confidence": round(confidence, 2),
        "risk_level": risk_level,
        "prediction_label": label,
        "affected_side": affected_side,
        "score_difference": round(score_diff, 2),
        "model_used": "asymmetry_threshold",
        "model_type": "threshold_based"
    }


# ========== UNIFIED PREDICTION FUNCTION ==========
def predict_stroke(patient_data):
    """
    Unified prediction function - tries ML model first, falls back to threshold
    """
    # Try ML model first
    ml_prediction = predict_with_model(patient_data)

    if ml_prediction is not None:
        return ml_prediction
    else:
        # Fall back to threshold method
        print("⚠️ Using fallback threshold prediction (ML model unavailable)")
        return predict_stroke_threshold(patient_data)


# ========== CONTROLLER API ==========

def get_sample_patients():
    global sample_patient_list
    if not sample_patient_list:
        sample_patient_list = add_sample_patients(5)
    return sample_patient_list
@app.route('/api/patients', methods=['GET'])  # To get all sample patients.
def api_get_sample_patients():
    patients = get_sample_patients()
    return jsonify({
        "success": True,
        "count": len(patients),
        "patients": [p.__dict__ for p in patients],
        "model_loaded": model is not None
    })


def clear_sample_patients():
    global sample_patient_list
    sample_patient_list = []
@app.route('/api/clear', methods=["GET"]) # To clear all sample patient data.
def api_clear_sample_patients():
    clear_sample_patients()
    return jsonify({
        "success": True,
        "message": "Cleared sample patients"
    })


def add_sample_patients(amount: int = 1):
    global sample_patient_list
    new_patients_list = []
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

        new_patient = Patient.create(patient, sensory_details)
        new_patients_list.append(new_patient)
        sample_patient_list.append(new_patient)
    return new_patients_list
@app.route('/api/generate-new/<int:amount>', methods=["GET"]) # To generate new fresh patient data.
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
            "new_patients": [p.__dict__ for p in new_patients],
            "model_loaded": model is not None
        })


@app.route('/api/predict', methods=['POST']) # Send patient's data to return a prediction.
def api_predict_stroke():
    try:
        if not request.values: # Get request body as JSON
            return jsonify({
                "success": False,
                "error": "No patient data provided"
            }), 400

        new_patient = PatientDetails(int(time.time()), request.values["age"], request.values["sex"],
                                     request.values["hypertension"], request.values["diabetes"], request.values["smoking"])

        left_score = float(request.values["left_sensory"])
        right_score = float(request.values["right_sensory"])
        asymmetry = abs(left_score - right_score) > 2.0
        if asymmetry: affected_side = "Left" if left_score < right_score else "Right"
        else: affected_side = "None"
        asymmetry_label = 1 if asymmetry else 0
        new_sensory = SensoryDetails(left_score, right_score, affected_side, asymmetry_label)

        patient = Patient.create(new_patient, new_sensory)

        prediction = predict_stroke(patient.__dict__)  # Get prediction from model/threshold

        # Add model status info
        prediction["model_loaded"] = model is not None

        return jsonify({
            "success": True,
            "prediction": prediction,
            "received_data": patient.__dict__,
            "model_status": "loaded" if model is not None else "not_loaded"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def get_dashboard_stats():
    patients = get_sample_patients()
    total = len(patients)

    # Calculate predictions for stats
    ml_predictions = 0
    risk_distribution = {"low": 0, "medium": 0, "high": 0}

    for p in patients:
        if hasattr(p, '__dict__'):
            patient_dict = p.__dict__
        else:
            patient_dict = p

        prediction = predict_stroke(patient_dict)
        risk_distribution[prediction["risk_level"]] += 1

        if prediction.get("model_used") == "trained_ml_model":
            ml_predictions += 1

    asymmetric = sum(1 for p in patients if getattr(p, 'asymmetry_label', 0) == 1)

    return {
        "total_patients": total,
        "asymmetric_cases": asymmetric,
        "asymmetric_percentage": (asymmetric/total*100) if total > 0 else 0,
        "avg_left_score": sum(p.left_sensory_score for p in patients)/total if total > 0 else 0,
        "avg_right_score": sum(p.right_sensory_score for p in patients)/total if total > 0 else 0,
        "ml_predictions": ml_predictions,
        "threshold_predictions": total - ml_predictions,
        "risk_distribution": risk_distribution,
        "model_loaded": model is not None
    }
@app.route('/api/dashboard', methods=['GET']) # To get the average statistics of the sample data.
def api_get_dashboard_stats(): # The statistics of the dashboard. for example: percentages
    return jsonify({
        "success": True,
        "dashboard": get_dashboard_stats(),
        "model_status": "loaded" if model is not None else "not_loaded"
    })


# ========== MODEL TEST ENDPOINT ==========
@app.route('/api/model-test', methods=['GET'])
def api_model_test():
    """Test endpoint to verify model is working"""
    test_cases = [
        {"left_sensory_score": 8.5, "right_sensory_score": 8.7},  # Normal
        {"left_sensory_score": 5.0, "right_sensory_score": 9.0},  # Unilateral
        {"left_sensory_score": 4.0, "right_sensory_score": 4.5},  # Bilateral
    ]

    results = []
    for i, test in enumerate(test_cases):
        prediction = predict_stroke(test)
        results.append({
            "test_case": i+1,
            "input": test,
            "prediction": prediction
        })

    return jsonify({
        "success": True,
        "model_loaded": model is not None,
        "model_path": MODEL_PATH if os.path.exists(MODEL_PATH) else "Not found",
        "test_results": results
    })


# ========== CONTROLLER PAGE ==========

@app.route('/') # Redirect url to the home page
def home():
    stats = get_dashboard_stats()
    patients = get_sample_patients()[:5]  # First 5 only for display

    # Get model predictions for display
    patient_predictions = []
    for p in patients:
        if hasattr(p, '__dict__'):
            pred = predict_stroke(p.__dict__)
        else:
            pred = predict_stroke(p)
        patient_predictions.append(pred)

    return render_template('index.html', stats=stats, patients=patients,
                           patient_predictions=patient_predictions, model_loaded=model is not None)

@app.route('/dataset') # Page to upload a dataset to view
def upload_dataset():
    return render_template('upload_dataset.html',model_loaded=model is not None)


# ========== MISC CONTROLLER ==========

@app.route('/status') # To check system status (fake)
def status():
    return jsonify({
        "status": "operational",
        "components": {
            "flask_app": "running",
            "data_module": "connected",
            "prediction_module": "ml_model" if model is not None else "threshold_fallback",
            "dashboard_module": "basic_stats",
            "ml_model_loaded": model is not None
        },
        "message": "Green: Flask is running." + (" ML model loaded successfully!" if model else " Using threshold fallback.")
    })


# ========== ERROR CONTROLLER ==========

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(_):
    return jsonify({"success": False, "error": "Internal server error"}), 500

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Bad request", "message": "Invalid input"}), 400

# ========== MAIN EXECUTION ==========

if __name__ == '__main__':
    print("=" * 50)
    print("LACUNAR STROKE DETECTION SYSTEM")
    print("=" * 50)

    # Model status
    if model:
        print(f"✅ ML Model: LOADED ({type(model).__name__})")
    else:
        print("⚠️ ML Model: NOT LOADED (using threshold fallback)")

    print("\n📊 Available endpoints:")
    print("   http://localhost:5000/              - Dashboard")
    print("   http://localhost:5000/status        - System status")
    print("   http://localhost:5000/api/patients  - Get all patients")
    print("   http://localhost:5000/api/generate-new/10 - Generate new patients")
    print("   http://localhost:5000/api/predict   - Make prediction (POST)")
    print("   http://localhost:5000/api/model-test - Test ML model")
    print("=" * 50)

    app.run(host="0.0.0.0", debug=True, port=5000)