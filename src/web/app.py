"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""
import logging
import time

import model.database as dbmanager
from model.sample.PatientDetails import PatientDetails

logging.basicConfig(level=logging.INFO)

from flask import Flask, render_template, jsonify, request, redirect, session
from src.model.auth import auth_bp  # Import auth blueprint
from src.model.notifications import notifications_bp  # Import notifications blueprint
import data_simulation.patient_generator as patient_gen
import random
import sys
import os
import joblib
import pandas as pd

from model.sample.Patient import Patient
from model.sample.SensoryDetails import SensoryDetails

current_dir = os.path.dirname(os.path.abspath(__file__))  # src/web/
parent_dir = os.path.dirname(current_dir)  # src/
sys.path.insert(0, parent_dir)


app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'your-secret-key-here-change-in-production')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(notifications_bp)

# ========== LOAD STROKE MODEL ==========
print("=" * 50)
print("🤖 LOADING STROKE PREDICTION MODEL")
print("=" * 50)

# Get the directory where app.py is (src/web/)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level to 'src/', then into 'model/'
MODEL_PATH = os.path.join(os.path.dirname(CURRENT_DIR), 'model', 'stroke_model.pkl')
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
    Unified Prediction Logic:
    - No Cliff-Edge (uses probability-weighted labels)
    - Side Detection
    - Bilateral Consideration
    """
    if model is None: return None

    try:
        # 1. Prepare Features
        left = float(patient_data.get("left_sensory_score"))
        right = float(patient_data.get("right_sensory_score"))
        avg = (left + right) / 2
        asymmetry_index = abs(left - right) / avg if avg > 0 else 0

        #Fetch Velocity from Database
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(patient_data.get("id", 0))
        score_velocity = min(l_vel, r_vel) # Capture the worst drop

        ht = int(patient_data.get("hypertension", 0))
        db = int(patient_data.get("diabetes", 0))
        sm = int(patient_data.get("smoking", 0))

        input_data = pd.DataFrame([[
            left, right, asymmetry_index,
            int(patient_data.get("hypertension", 0)),
            int(patient_data.get("diabetes", 0)),
            int(patient_data.get("smoking", 0)),
            score_velocity
        ]], columns=['left_sensory_score', 'right_sensory_score', 'asymmetry_index',
                     'hypertension', 'diabetes', 'smoking_history', 'score_velocity'])

        # 2. Get Prediction and Probabilities (To avoid cliff-edges)
        prediction_code = int(model.predict(input_data)[0])
        probs = model.predict_proba(input_data)[0]
        confidence = max(probs)

        # 3. Determine Affected Side & Bilateral Risk
        # Even if model says unilateral, if both scores are low, it's Bilateral
        if left < 6.0 and right < 6.0:
            affected_side = "Bilateral (Both Sides)"
            # Smooth transition to Bilateral if both are low
            if prediction_code != 4 and confidence < 0.7:
                prediction_code = 4
        elif left < right - 0.5:
            affected_side = "Left"
        elif right < left - 0.5:
            affected_side = "Right"
        else:
            affected_side = "None"

        if score_velocity < -1.0:
            prediction_code = 4

        # 4. Clinical Label Mapping (Based on your IMPACT_LEVELS)
        impact_labels = {
            0: {"label": "Strong Response", "level": "low", "emoji": "🟢"},
            1: {"label": "Slightly Reduced", "level": "medium", "emoji": "🟡"},
            2: {"label": "Moderately Reduced", "level": "medium", "emoji": "🟠"},
            3: {"label": "Significantly Reduced", "level": "high", "emoji": "🔴"},
            4: {"label": "Weak Global Response", "level": "critical", "emoji": "🟣"}
        }

        res = impact_labels.get(prediction_code)

        # 5. Cliff-Edge Smoothing:
        # If confidence is low, we soften the label to "Borderline"
        # so the user isn't startled by a sudden change.
        display_label = res["label"]
        if confidence < 0.55:
            display_label = f"Borderline {display_label}"

        return {
            "prediction_code": prediction_code,
            "sensory_response": display_label,
            "risk_level": res["level"],
            "state_emoji": res["emoji"],
            "affected_side": affected_side,
            "model_confidence": round(confidence, 2),
            "asymmetry_index": round(asymmetry_index, 3),
            "is_bilateral": prediction_code == 4 or affected_side == "Bilateral (Both Sides)"
        }

    except Exception as e:
        print(f"❌ Model prediction error: {e}")
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
    for i in range(amount):
        patient_detail = patient_gen.generate_single_patient_details(random.randint(100, 999))
        sensory_detail = patient_gen.generate_single_sensory_details(patient_detail)

        new_patient = Patient.create(patient_detail, sensory_detail)
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
        # 1. Check for incoming data
        if not request.values:
            return jsonify({
                "success": False,
                "error": "No patient data provided"
            }), 400

        # 2. Reconstruct Patient Details from form/request
        # We try to get an ID; if it's a new patient, we use a temporary timestamp-based ID
        patient_id = int(request.values.get("patient_id", int(time.time())))

        new_patient_details = PatientDetails(
            patient_id,
            request.values["age"],
            request.values["sex"],
            int(request.values["hypertension"]),
            int(request.values["diabetes"]),
            int(request.values["smoking"])
        )

        # 3. Extract Sensory Scores
        left_score = float(request.values["left_asymmetry"])
        right_score = float(request.values["right_asymmetry"])

        # 4. FETCH BASELINE & VELOCITY: Historical Context from database.py
        # This allows us to see if the current score is a sudden drop
        from model.database import get_patient_baseline, get_reading_velocity
        baseline = get_patient_baseline(patient_id)
        l_vel, r_vel, t_delta = get_reading_velocity(patient_id)

        # Determine the worst velocity (largest drop)
        current_velocity = min(l_vel, r_vel)

        # 5. Determine Affected Side (Initial Logic)
        asymmetry_detected = abs(left_score - right_score) > 2.0
        asymmetry_label = 1 if asymmetry_detected else 0

        if left_score < right_score - 0.5:
            affected_side = "Left"
        elif right_score < left_score - 0.5:
            affected_side = "Right"
        else:
            affected_side = "None"

        # 6. Create SensoryDetails and Patient Object
        # We pass the calculated velocity into the sensory object
        new_sensory = SensoryDetails(
            left_score,
            right_score,
            affected_side,
            asymmetry_label,
            score_velocity=current_velocity
        )

        # Create the unified patient object
        patient = Patient.create(new_patient_details, new_sensory)

        # 7. Add context data for the prediction function
        patient_dict = patient.__dict__
        patient_dict['baseline'] = baseline # Pass baseline for cliff-edge check
        patient_dict['id'] = patient_id

        # 8. EXECUTE PREDICTION: Calls ML model with Velocity and Baseline context
        prediction = predict_stroke(patient_dict)

        # 9. Add metadata for the UI
        prediction["model_loaded"] = model is not None
        prediction["velocity_detected"] = current_velocity
        prediction["time_since_last_reading"] = t_delta

        # Construct final response
        data = jsonify({
            "success": True,
            "prediction": prediction,
            "received_data": patient_dict,
            "model_status": "loaded" if model is not None else "not_loaded"
        }).json

        print(f"📊 Prediction Result for Patient {patient_id}: {prediction['sensory_response']}")

        return render_template('result.html', data=data, model_loaded=model is not None)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


def get_dashboard_stats():
    patients = get_sample_patients()
    total = len(patients)

    # Calculate predictions for stats
    ml_predictions = 0
    risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}

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
    return render_template('index.html', model_loaded=model is not None)

# Replace your current login/register routes with:
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handle login page - auth logic is in auth.py"""
    if 'user_id' in session:
        # Redirect to appropriate dashboard if already logged in
        if session.get('role') == 'doctor':
            return redirect('/dashboard/doctor')
        else:
            return redirect('/dashboard/patient/' + session.get('user_id'))
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    """Handle register page - auth logic is in auth.py"""
    if 'user_id' in session:
        # Redirect if already logged in
        return redirect('/')
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Handle logout"""
    session.clear()
    return redirect('/')

@app.route('/dashboard/doctor')
def doctor_dashboard():
    """Doctor dashboard"""
    if 'user_id' not in session or session.get('role') != 'doctor':
        return redirect('/login')
    try:
        user_id = session['user_id']
        doctor_info = dbmanager.getByID('doctor_info', user_id) if dbmanager.getByID('doctor_info', user_id) else None
        patients = dbmanager.getAllWhere('patient_info', 'doctor_id = ?', user_id)[:10]  # First 10 patients
        notifications = dbmanager.getAllWhere('notification', '1=1 ORDER BY timestamp DESC')[:5]
        return render_template('dashboard_doctor.html',
                               doctor=doctor_info,
                               patients=patients,
                               notifications=notifications,
                               user_email=session.get('email'))
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard_doctor.html', error=str(e))

@app.route('/exception-report')
def exception_report():
    if 'user_id' not in session or session.get('role') != 'doctor':
        return redirect('/login')
    try:
        exception_list = dbmanager.getAll('exception_report')
        critical_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Critical')
        borderline_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Borderline')
        normal_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Normal')
    
        avg_asym = round(sum(exception.highest_reading_asymmetry_index for exception in exception_list) / len(exception_list) * 100, 2)

        filtered_exception_list = [exception for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label in ['Critical', 'Borderline']]

        return render_template('exception_report.html', exception_list=filtered_exception_list, criticalcount=critical_count, borderlinecount=borderline_count, normalcount=normal_count, avg_asym=avg_asym,
                           model_loaded=model is not None)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('exception_report.html', error=str(e))


@app.route('/dashboard/patient')
def default_dashboard():
    return redirect('/login')

@app.route('/dashboard/patient/<string:patient_id>')
def dashboard_patient(patient_id):
    if 'user_id' not in session or session.get('role') != 'doctor' and patient_id != session['user_id']:
        return redirect('/login')
    try:
        patient_info = dbmanager.getByID('exception_report', patient_id)
        readings = dbmanager.getAllWhere('detailed_reading', 'patient_id = ?', patient_id)
        notifs = dbmanager.getAllWhere('notification', 'patient_id = ?', patient_id)
        return render_template('dashboard_patient.html',patient=patient_info,readings=readings, notifs=notifs,model_loaded=model is not None)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard_patient.html', error=str(e))


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

@app.route('/dataset') # Page to upload a dataset to view
def upload_dataset():
    return render_template('upload_dataset.html',model_loaded=model is not None)

@app.route('/result')
def result():
    return render_template('result.html',model_loaded=model is not None)

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