"""
Main Flask App for Lacunar Stroke Detection
Green: This is the foundation. Other members add to marked sections.
"""
import logging

from datetime import datetime
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
import numpy as np


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


# ========== VOLATILITY CALCULATION ==========
def calculate_stuttering_volatility(patient_id, current_avg_score):
    """
    Calculates the Volatility Index (Standard Deviation of recent readings).
    Detects the 'stuttering pattern' characteristic of active lacunar strokes.
    """
    try:
        history = dbmanager.getAllWhere('reading', 'patient_id = %s', patient_id)
        if not history or len(history) < 2:
            return 0.0

        # Take the last 4 readings from DB + the current score
        history.sort(key=lambda x: x.timestamp, reverse=True)
        recent_scores = [(float(r.left_sensory_score) + float(r.right_sensory_score))/2 for r in history[:4]]
        recent_scores.append(current_avg_score)

        return float(np.std(recent_scores))
    except Exception: return 0.0


# ========== MODEL PREDICTION FUNCTION ==========
def encode_diabetes_type(diabetes_type):
    """Encode diabetes type to numerical values"""
    encoding = {
        "None": 0,
        "Type 1": 1,
        "Type 2": 2,
        "Gestational": 3,
        "Prediabetes": 4,
        "Other": 5
    }
    return encoding.get(diabetes_type, 0)

def encode_bp_category(bp_category):
    """Encode BP category to numerical values"""
    encoding = {
        "Normal": 0,
        "Elevated": 1,
        "Hypertension Stage 1": 2,
        "Hypertension Stage 2": 3,
        "Hypertensive Crisis": 4
    }
    return encoding.get(bp_category, 0)


def predict_with_model(patient_data):
    """
    Unified Prediction Logic:
    - No Cliff-Edge (uses probability-weighted labels)
    - Side Detection
    - Bilateral Consideration
    """
    if model is None:
        return None

    try:
        # 1. Prepare Features
        left = float(patient_data.get("left_sensory_score"))
        right = float(patient_data.get("right_sensory_score"))
        avg = (left + right) / 2
        asymmetry_index = abs(left - right) / (avg + 1)  # +1 to avoid division by zero

        # Fetch Velocity from Database
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(patient_data.get("id", 0))

        # Determine which velocity to use based on affected side
        affected_side = "None"
        if left < right - 0.5:
            affected_side = "Left"
            score_velocity = l_vel if l_vel is not None else 0
        elif right < left - 0.5:
            affected_side = "Right"
            score_velocity = r_vel if r_vel is not None else 0
        else:
            score_velocity = min(l_vel, r_vel) if (l_vel is not None and r_vel is not None) else 0

        score_velocity = round(score_velocity, 6)

        volatility = calculate_stuttering_volatility(patient_data.get("id"), avg)

        # Get all required features from patient_data
        sbp = float(patient_data.get("systolic_bp", 120))
        dbp = float(patient_data.get("diastolic_bp", 80))  # NEW
        hba1c = float(patient_data.get("hba1c", 5.4))
        blood_glucose = float(patient_data.get("blood_glucose", 100))  # NEW
        diabetes_type = patient_data.get("diabetes_type", "None")  # NEW
        bp_category = patient_data.get("bp_category", "Normal")  # NEW
        on_bp_medication = int(patient_data.get("on_bp_medication", 0))  # NEW
        sm = int(patient_data.get("smoking_history", patient_data.get("smoking", 0)))

        # Encode categorical variables
        diabetes_type_encoded = encode_diabetes_type(diabetes_type)  # You need to define this
        bp_category_encoded = encode_bp_category(bp_category)  # You need to define this

        # 2. Create input data with ALL expected features
        input_data = pd.DataFrame([[
            left, right, asymmetry_index, sbp, dbp, hba1c, blood_glucose,
            diabetes_type_encoded, bp_category_encoded, on_bp_medication,
            sm, score_velocity, volatility
        ]], columns=[
            'left_sensory_score', 'right_sensory_score', 'asymmetry_index',
            'systolic_bp', 'diastolic_bp', 'hba1c', 'blood_glucose',
            'diabetes_type', 'bp_category', 'on_bp_medication',
            'smoking_history', 'score_velocity', 'volatility_index'
        ])

        # 3. Get Prediction and Probabilities
        prediction_code = int(model.predict(input_data)[0])
        probs = model.predict_proba(input_data)[0]
        confidence = max(probs)

        # 4. Post-processing rules
        # Override to bilateral if volatility high and velocity negative
        if volatility > 1.2 and score_velocity < -0.8:
            prediction_code = 4

        # 5. Determine Affected Side & Bilateral Risk
        # Re-evaluate affected side after potential override
        if prediction_code == 4 or (left < 6.0 and right < 6.0):
            affected_side = "Bilateral (Both Sides)"
        elif left < right - 0.5:
            affected_side = "Left"
        elif right < left - 0.5:
            affected_side = "Right"
        else:
            affected_side = "None"

        # 6. Clinical Label Mapping
        impact_labels = {
            0: {"label": "Strong Response", "level": "low", "emoji": "🟢"},
            1: {"label": "Slightly Reduced", "level": "medium", "emoji": "🟡"},
            2: {"label": "Moderately Reduced", "level": "medium", "emoji": "🟠"},
            3: {"label": "Significantly Reduced", "level": "high", "emoji": "🔴"},
            4: {"label": "Weak Global Response", "level": "critical", "emoji": "🟣"}
        }

        res = impact_labels.get(prediction_code, impact_labels[0])

        # 7. Cliff-Edge Smoothing
        display_label = res["label"]
        if confidence < 0.55:
            display_label = f"Borderline {display_label}"

        # Add confidence-based qualifier
        if confidence < 0.4:
            display_label = f"Low Confidence: {display_label}"

        return {
            "prediction_code": prediction_code,
            "sensory_response": display_label,
            "risk_level": res["level"],
            "state_emoji": res["emoji"],
            "affected_side": affected_side,
            "model_confidence": round(confidence, 3),
            "asymmetry_index": round(asymmetry_index, 3),
            "volatility": round(volatility, 3),
            "score_velocity": score_velocity,
            "features_used": len(input_data.columns)
        }

    except Exception as ex:
        print(f"❌ Model prediction error: {ex}")
        import traceback
        traceback.print_exc()
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


@app.route('/predict-form')
def predict_form():
    """Show the dedicated prediction form for logged-in patients"""
    if 'user_id' not in session:
        return redirect('/login')

    # Check if user is a patient (user in database = patient in your system)
    role = session.get('role', '').lower()

    if role != 'user':  # Changed from 'PATIENT' to 'user'
        if role == 'doctor':
            return redirect('/dashboard/doctor')
        else:
            return redirect('/')

    # Get patient info for the form
    user_id = session['user_id']
    patient_info = dbmanager.getByID('patient_info', user_id)

    patient_name = ""
    if patient_info:
        if hasattr(patient_info, 'first_name') and patient_info.first_name:
            patient_name = patient_info.first_name
            if hasattr(patient_info, 'last_name') and patient_info.last_name:
                patient_name += f" {patient_info.last_name}"

    return render_template('predict_form.html',
                           patient_name=patient_name,
                           model_loaded=model is not None)

@app.route('/api/predict', methods=['POST'])
def api_predict_stroke():
    """
    Handles stroke prediction with comprehensive error handling.
    Checks for session validity, input integrity, and processing errors.
    """
    try:
        # 1. Authentication Check
        if 'user_id' not in session:
            logging.warning("Unauthorized access attempt to /api/predict")
            return render_template('error.html',
                                   error="Your session has expired. Please log in again.",
                                   redirect_url="/login"), 401

        user_id = session['user_id']

        # 2. Database Integrity Check
        patient_info = dbmanager.getByID('patient_info', user_id)
        if not patient_info:
            logging.error(f"Patient info missing for user_id: {user_id}")
            return render_template('error.html',
                                   error="Patient profile not found. Please complete your profile settings."), 404

        # 3. Input Extraction and Validation - EXPANDED for new fields
        try:
            left_score = float(request.form.get("left_asymmetry", 9.0))
            right_score = float(request.form.get("right_asymmetry", 9.0))

            # Ensure scores are within clinical bounds (0.0 to 10.0)
            if not (0 <= left_score <= 10 and 0 <= right_score <= 10):
                raise ValueError("Sensory scores must be between 0 and 10.")

            # Get all required fields with fallbacks
            sbp = float(request.form.get("systolic_bp") or getattr(patient_info, 'systolic_bp', 120))
            dbp = float(request.form.get("diastolic_bp") or getattr(patient_info, 'diastolic_bp', 80))
            hba1c = float(request.form.get("hba1c") or getattr(patient_info, 'hba1c', 5.4))
            blood_glucose = float(request.form.get("blood_glucose") or getattr(patient_info, 'blood_glucose', 100))
            smoking = int(request.form.get("smoking") or getattr(patient_info, 'smoking_history', 0))

            # Categorical fields
            diabetes_type = request.form.get("diabetes_type") or getattr(patient_info, 'diabetes_type', 'None')
            bp_category = request.form.get("bp_category") or getattr(patient_info, 'bp_category', 'Normal')
            on_bp_medication = int(request.form.get("on_bp_medication") or getattr(patient_info, 'on_bp_medication', 0))

            # Validate ranges
            if not (60 <= dbp <= 130):
                raise ValueError("Diastolic BP must be between 60 and 130 mmHg")
            if not (70 <= blood_glucose <= 500):
                raise ValueError("Blood glucose must be between 70 and 500 mg/dL")

        except ValueError as ve:
            logging.error(f"Validation Error: {ve}")
            return render_template('error.html', error=f"Invalid input data: {str(ve)}"), 400

        # 4. Object Creation and Processing - FIXED to match new PatientDetails
        new_patient_details = PatientDetails(
            patient_id=user_id,
            age_group=request.form.get("age_group") or getattr(patient_info, 'age_group', '50-59'),
            sex=request.form.get("sex") or getattr(patient_info, 'sex', 'Male'),
            systolic_bp=sbp,
            hba1c=hba1c,
            smoking_history=smoking,
            diastolic_bp=dbp,
            blood_glucose=blood_glucose,
            diabetes_type=diabetes_type,
            bp_category=bp_category,
            on_bp_medication=on_bp_medication
        )

        # Calculate temporal features
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(user_id)
        current_velocity = min(l_vel, r_vel) if (l_vel is not None and r_vel is not None) else 0.0

        avg_score = (left_score + right_score) / 2
        volatility = calculate_stuttering_volatility(user_id, avg_score)

        # Calculate asymmetry index
        asymmetry_index = abs(left_score - right_score) / (avg_score + 1)

        new_sensory = SensoryDetails(
            left_sensory_score=left_score,
            right_sensory_score=right_score,
            systolic_bp=sbp,
            hba1c=hba1c,
            affected_side="Determined by Model",
            asymmetry_label=1 if abs(left_score - right_score) > 2.0 else 0,
            score_velocity=current_velocity,
            volatility_index=volatility
        )

        # 5. Prediction Logic - Updated with all 13 features
        patient_dict = {
            "id": user_id,
            "patient_id": user_id,
            "left_sensory_score": left_score,
            "right_sensory_score": right_score,
            "systolic_bp": sbp,
            "diastolic_bp": dbp,
            "hba1c": hba1c,
            "blood_glucose": blood_glucose,
            "diabetes_type": diabetes_type,
            "bp_category": bp_category,
            "on_bp_medication": on_bp_medication,
            "smoking": smoking,
            "smoking_history": smoking,
            "score_velocity": current_velocity,
            "volatility": volatility,
            "asymmetry_index": asymmetry_index
        }

        # Attempt ML Prediction, fallback to Threshold if model is missing or fails
        prediction = None
        if model:
            try:
                prediction = predict_with_model(patient_dict)
            except Exception as e:
                logging.error(f"ML Prediction failed, falling back: {e}")
                import traceback
                traceback.print_exc()

        if not prediction:
            prediction = predict_stroke_threshold(patient_dict)

        # 6. Database Persistence - UPDATED for new Reading class
        try:
            from model.db.Reading import Reading
            reading = Reading(
                patient_id=user_id,
                timestamp=datetime.now(),
                left_sensory_score=left_score,
                right_sensory_score=right_score,
                systolic_bp=sbp,
                diastolic_bp=dbp,
                hba1c=hba1c,
                blood_glucose=blood_glucose,
                diabetes_type=diabetes_type,
                bp_category=bp_category,
                on_bp_medication=on_bp_medication
            )

            # Add calculated fields
            reading.asymmetry_index = asymmetry_index
            reading.score_velocity = current_velocity
            reading.volatility_index = volatility

            # Add prediction results if available
            if prediction:
                reading.prediction_tier = prediction.get('prediction_code')
                reading.risk_label = prediction.get('sensory_response')
                reading.affected_side = prediction.get('affected_side')
                reading.model_confidence = prediction.get('model_confidence')

            dbmanager.insert('reading', reading)
        except Exception as db_err:
            logging.error(f"Failed to save reading to database: {db_err}")
            import traceback
            traceback.print_exc()
            # We continue even if saving fails so the user gets their immediate result

        return render_template('result.html',
                               data={"prediction": prediction,
                                     "timestamp": datetime.now(),
                                     "patient_data": {
                                         "scores": {"left": left_score, "right": right_score},
                                         "bp": {"systolic": sbp, "diastolic": dbp},
                                         "glucose": {"hba1c": hba1c, "blood_glucose": blood_glucose},
                                         "conditions": {"diabetes_type": diabetes_type,
                                                        "bp_category": bp_category}
                                     }},
                               model_loaded=(model is not None))

    except Exception as ex:
        logging.critical(f"Uncaught Exception in api_predict_stroke: {ex}", exc_info=True)
        import traceback
        traceback.print_exc()
        return render_template('error.html',
                               error="An unexpected system error occurred. Our team has been notified."), 500


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

@app.route('/api/save-reading', methods=['POST'])
def save_reading():
    try:
        if 'user_id' not in session:
            return jsonify({"success": False, "error": "Not logged in"}), 401

        data = request.json
        patient_id = session['user_id']

        # Create Reading object
        from model.db.Reading import Reading
        from datetime import datetime

        reading = Reading(
            patient_id=patient_id,
            timestamp=datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00')),
            left_sensory_score=float(data['left_sensory_score']),
            right_sensory_score=float(data['right_sensory_score'])
        )

        # Save to database
        reading_id = dbmanager.insert('reading', reading)

        # Trigger prediction (optional)
        patient_data = {
            "id": patient_id,
            "left_sensory_score": float(data['left_sensory_score']),
            "right_sensory_score": float(data['right_sensory_score'])
        }

        # Get additional patient info if needed
        patient_info = dbmanager.getByID('patient_info', patient_id)
        if patient_info:
            patient_data.update({
                "age": getattr(patient_info, 'age', '50-59'),
                "sex": getattr(patient_info, 'sex', 'Male'),
                "hypertension": int(getattr(patient_info, 'hypertension', 0)),
                "diabetes": int(getattr(patient_info, 'diabetes', 0)),
                "smoking": int(getattr(patient_info, 'smoking_history', 0))
            })

        prediction = predict_stroke(patient_data)

        return jsonify({
            "success": True,
            "reading_id": reading_id,
            "prediction": prediction,
            "message": "Reading saved successfully"
        })

    except Exception as ex:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(ex)}), 500

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

@app.route('/')
def home():
    """Redirect to appropriate dashboard if logged in"""
    if 'user_id' in session:
        if session.get('role') == 'DOCTOR':
            return redirect('/dashboard/doctor')
        else:
            return redirect('/dashboard/patient')
    return render_template('index.html', model_loaded=model is not None)


# Replace your current login/register routes with:
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Handle login page - auth logic is in auth.py"""
    if 'user_id' in session:
        # Redirect to appropriate dashboard if already logged in
        if session['role'] == 'DOCTOR':
            return redirect('/dashboard/doctor')
        else:
            return redirect('/dashboard/patient/' + str(session['user_id']))
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
    try:
        if 'user_id' not in session or session['role'] != 'DOCTOR':
            return redirect('/login')
        user_id = session['user_id']
        doctor_info = dbmanager.getByID('doctor_info', user_id) if dbmanager.getByID('doctor_info', user_id) else None
        patients = dbmanager.getAllWhere('patient_report', 'doctor_id = ?', user_id)

        critical_count = sum(1 for exception in patients if hasattr(exception, 'latest_reading_risk_label') and exception.latest_reading_risk_label == 'Critical') if patients else 0
        borderline_count = sum(1 for exception in patients if hasattr(exception, 'latest_reading_risk_label') and exception.latest_reading_risk_label == 'Borderline') if patients else 0
        normal_count = sum(1 for exception in patients if hasattr(exception, 'latest_reading_risk_label') and exception.latest_reading_risk_label == 'Normal') if patients else 0

        notifications = dbmanager.callProcedure('notification','call GetCriticalAlert(?)', user_id)
        alertsCount = sum(1 for exception in notifications if hasattr(exception, 'id') and exception.type == 'Critical') if notifications else 0

        return render_template('dashboard_doctor.html',
                               doctor=doctor_info, patients=patients, patient_json=(patient.__dict__ for patient  in patients),
                               criticalcount=critical_count, borderlinecount=borderline_count, normalcount=normal_count, alertscount=alertsCount,
                               notifications=notifications)
    except Exception as ex:
        print(f"Dashboard error: {ex}")
        return render_template('exception_report.html', error=str(e))

@app.route('/exception-report') # Allow doctors to go to a list of critical patients
def exception_report():
    if 'user_id' not in session or session['role'] != 'DOCTOR':
        return redirect('/login')
    exception_list = dbmanager.getAll('patient_report')
    critical_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Critical')
    borderline_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Borderline')
    normal_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Normal')

    avg_asym = round(sum(exception.highest_reading_asymmetry_index for exception in exception_list) / len(exception_list) * 100, 2)

    filtered_exception_list = [exception for exception in exception_list if hasattr(exception, 'latest_reading_risk_label') and exception.latest_reading_risk_label in ['Critical', 'Borderline']]

    return render_template('exception_report.html', exception_list=filtered_exception_list, criticalcount=critical_count, borderlinecount=borderline_count, normalcount=normal_count, avg_asym=avg_asym,
                           model_loaded=model is not None)

@app.route('/dashboard/patient') # Default dashboard will send a doctor to his dashboard, and a patient to his dashboard.
def default_dashboard():
    try:
        if 'user_id' not in session:  return redirect('/login')
        if session['role'] != 'USER': return redirect('/dashboard/doctor')

        return redirect(f'/dashboard/patient/{session['user_id']}')
    except Exception as ex:
        print(f"Patient dashboard error: {ex}")
        return render_template('error.html', error=str(ex))

@app.route('/dashboard/patient/<string:patient_id>')
def dashboard_patient(patient_id):
        if 'user_id' not in session:
            return redirect('/login')

        # Check access permissions
        if session['role'] == 'USER' and str(session['user_id']) != str(patient_id):
            return render_template('error.html', error="You don't have permission to view this dashboard",  redirect_url=f"/dashboard/patient/{patient_id}"), 403

        patient_info = dbmanager.getByID('patient_report', patient_id)
        readings = dbmanager.getAllWhere('detailed_reading', 'patient_id = ?', patient_id)
        notifs = dbmanager.getAllWhere('notification', 'patient_id = ?', patient_id)
        return render_template('dashboard_patient.html',patient=patient_info, readings=readings, notifs=notifs,model_loaded=model is not None)


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

from flask import send_from_directory

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

# ========== ERROR CONTROLLER ==========

@app.errorhandler(404)
def not_found(_):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def server_error(_):
    return jsonify({"success": False, "error": "Internal server error"}), 500

@app.errorhandler(400)
def bad_request(ex):
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