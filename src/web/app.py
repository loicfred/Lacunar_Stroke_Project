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
        asymmetry_index = abs(left - right) / (avg + 1)  # Your +1 fix

        #Fetch Velocity from Database
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(patient_data.get("id", 0))
        score_velocity = min(l_vel, r_vel) # Capture the worst drop

        ht = int(patient_data.get("hypertension", 0))
        db = int(patient_data.get("diabetes", 0))
        sm = int(patient_data.get("smoking", 0))

        input_data = pd.DataFrame([[
            left, right, asymmetry_index,ht, db, sm, score_velocity
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

    except Exception as ex:
        print(f"❌ Model prediction error: {ex}")
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
    try:
        # 1. Check if user is logged in
        if 'user_id' not in session:
            return render_template('error.html',
                                   error="Please login first to use the prediction system.",
                                   redirect_url="/login"), 401

        user_id = session['user_id']
        user_role = session.get('role', 'user').lower()  # Default to 'user'

        # 2. Get patient info from database (for default values if form doesn't provide)
        patient_info = dbmanager.getByID('patient_info', user_id)
        if not patient_info:
            return render_template('error.html',
                                   error="Patient information not found. Please contact support.",
                                   redirect_url="/"), 404

        # 3. Extract Sensory Scores AND Health Factors from form
        left_score_str = request.form.get("left_asymmetry", "5.0")
        right_score_str = request.form.get("right_asymmetry", "5.0")

        # Get health factors from form (for test cases - priority over database)
        hypertension_form = request.form.get("hypertension", None)
        diabetes_form = request.form.get("diabetes", None)
        smoking_form = request.form.get("smoking", None)

        # Get demographic info from form (for test cases)
        age_group_form = request.form.get("age_group", None)
        sex_form = request.form.get("sex", None)

        # Convert sensory scores to float with error handling
        try:
            left_score = float(left_score_str)
        except ValueError:
            left_score = 5.0  # Default value

        try:
            right_score = float(right_score_str)
        except ValueError:
            right_score = 5.0  # Default value

        # 4. Determine health factor values (form takes priority, then database)
        if hypertension_form is not None:
            try:
                hypertension_val = int(hypertension_form)
            except:
                hypertension_val = int(getattr(patient_info, 'hypertension', 0))
        else:
            hypertension_val = int(getattr(patient_info, 'hypertension', 0))

        if diabetes_form is not None:
            try:
                diabetes_val = int(diabetes_form)
            except:
                diabetes_val = int(getattr(patient_info, 'diabetes', 0))
        else:
            diabetes_val = int(getattr(patient_info, 'diabetes', 0))

        if smoking_form is not None:
            try:
                smoking_val = int(smoking_form)
            except:
                smoking_val = int(getattr(patient_info, 'smoking_history', 0))
        else:
            smoking_val = int(getattr(patient_info, 'smoking_history', 0))

        # Determine age and sex (form takes priority)
        age_val = age_group_form if age_group_form else getattr(patient_info, 'age', '50-59')
        sex_val = sex_form if sex_form else getattr(patient_info, 'sex', 'Male')

        # 5. Create PatientDetails object USING FORM DATA for test cases
        new_patient_details = PatientDetails(
            user_id,
            age_val,          # From form or database
            sex_val,          # From form or database
            hypertension_val,  # Use form value for test cases
            diabetes_val,      # Use form value for test cases
            smoking_val        # Use form value for test cases
        )

        # 6. Determine affected side
        if left_score < right_score - 0.5:
            affected_side = "Left"
        elif right_score < left_score - 0.5:
            affected_side = "Right"
        else:
            affected_side = "None"

        asymmetry_label = 1 if abs(left_score - right_score) > 2.0 else 0

        # 7. Get baseline and velocity
        from model.database import get_patient_baseline, get_reading_velocity
        baseline = get_patient_baseline(user_id)
        l_vel, r_vel, t_delta = get_reading_velocity(user_id)
        current_velocity = min(l_vel, r_vel) if l_vel and r_vel else 0.0

        # 8. Create SensoryDetails with velocity
        new_sensory = SensoryDetails(
            left_score,
            right_score,
            affected_side,
            asymmetry_label,
            score_velocity=current_velocity
        )

        # 9. Create Patient object
        patient = Patient.create(new_patient_details, new_sensory)

        # 10. Save reading to database
        from model.db.Reading import Reading
        from datetime import datetime

        reading = Reading(
            patient_id=user_id,
            timestamp=datetime.now(),
            left_sensory_score=float(left_score),  # Ensure float
            right_sensory_score=float(right_score)  # Ensure float
        )
        reading_id = dbmanager.insert('reading', reading)

        # 11. Prepare data for prediction
        patient_dict = patient.__dict__
        patient_dict['baseline'] = baseline
        patient_dict['id'] = user_id
        patient_dict['score_velocity'] = current_velocity
        patient_dict['hypertension'] = hypertension_val  # Use the determined value
        patient_dict['diabetes'] = diabetes_val          # Use the determined value
        patient_dict['smoking'] = smoking_val            # Use the determined value

        # 12. Execute prediction
        prediction = predict_stroke(patient_dict)

        # 13. Add metadata
        prediction["reading_id"] = reading_id
        prediction["model_loaded"] = model is not None
        prediction["velocity_detected"] = current_velocity
        prediction["time_since_last_reading"] = t_delta

        # Add clinical category for template
        prediction["clinical_category"] = "Unilateral" if prediction.get("affected_side") in ["Left", "Right"] \
            else "Bilateral" if prediction.get("affected_side") == "Bilateral (Both Sides)" \
            else "Normal"

        # Add prediction_label for template
        prediction["prediction_label"] = prediction.get("sensory_response", "Unknown")

        # 14. Get patient name
        patient_name = ""
        if hasattr(patient_info, 'first_name') and patient_info.first_name:
            patient_name = patient_info.first_name
            if hasattr(patient_info, 'last_name') and patient_info.last_name:
                patient_name += f" {patient_info.last_name}"

        # 15. Prepare response data
        response_data = {
            "success": True,
            "prediction": prediction,
            "patient": {
                "id": user_id,
                "name": patient_name,
                "age": age_val,
                "sex": sex_val
            },
            "sensory_scores": {
                "left": left_score,
                "right": right_score,
                "asymmetry": round(abs(left_score - right_score), 2)
            },
            "health_factors": {
                "hypertension": bool(hypertension_val),
                "diabetes": bool(diabetes_val),
                "smoking": bool(smoking_val)
            },
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_used": "ML Model" if model is not None else "Threshold Analysis",
            "reading_id": reading_id
        }

        return render_template('result.html',
                               data=response_data,
                               model_loaded=model is not None)

    except Exception as ex:
        import traceback
        traceback.print_exc()  # This will print full traceback to console
        return render_template('error.html',
                               error=f"Prediction error: {str(ex)}",
                               redirect_url="/"), 500


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
                               doctor=doctor_info, patients=patients,
                               criticalcount=critical_count, borderlinecount=borderline_count, normalcount=normal_count, alertscount=alertsCount,
                               notifications=notifications)
    except Exception as ex:
        print(f"Dashboard error: {ex}")
        return render_template('exception_report.html', error=str(e))

@app.route('/exception-report')
def exception_report():

    exception_list = dbmanager.getAll('patient_report')
    critical_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Critical')
    borderline_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Borderline')
    normal_count = sum(1 for exception in exception_list if hasattr(exception, 'avg_risk_label') and exception.avg_risk_label == 'Normal')

    avg_asym = round(sum(exception.highest_reading_asymmetry_index for exception in exception_list) / len(exception_list) * 100, 2)

    filtered_exception_list = [exception for exception in exception_list if hasattr(exception, 'latest_reading_risk_label') and exception.latest_reading_risk_label in ['Critical', 'Borderline']]

    return render_template('exception_report.html', exception_list=filtered_exception_list, criticalcount=critical_count, borderlinecount=borderline_count, normalcount=normal_count, avg_asym=avg_asym,
                           model_loaded=model is not None)

@app.route('/dashboard/patient')
def patient_dashboard():
    """
    Default patient dashboard - shows the logged-in patient's own dashboard
    """
    try:
        if 'user_id' not in session:
            return redirect('/login')

        # Check if user is a patient (user = patient)
        if session.get('role', '').lower() != 'user':  # Changed here
            # If doctor, redirect them to their own dashboard
            if session.get('role', '').lower() == 'doctor':
                return redirect('/dashboard/doctor')
            else:
                return redirect('/login')

        patient_id = session['user_id']
        return redirect(f'/dashboard/patient/{patient_id}')

    except Exception as ex:
        print(f"Patient dashboard error: {ex}")
        return render_template('error.html', error=str(ex))

@app.route('/dashboard/patient/<string:patient_id>')
def dashboard_patient(patient_id):
    """
    View patient dashboard - accessible by both the patient themselves and doctors
    """
    try:
        if 'user_id' not in session:
            return redirect('/login')

        user_id = session['user_id']
        user_role = session.get('role', '').lower()  # Get and lowercase

        # Check access permissions
        if user_role == 'user' and str(user_id) != str(patient_id):  # Changed here
            return render_template('error.html',
                                   error="You don't have permission to view this dashboard",
                                   redirect_url=f"/dashboard/patient/{user_id}"), 403

        # Get patient basic info
        patient_basic_info = dbmanager.getByID('patient_info', patient_id)

        if not patient_basic_info:
            return render_template('error.html',
                                   error=f"Patient with ID {patient_id} not found",
                                   redirect_url="/dashboard/doctor" if user_role == 'DOCTOR' else "/"), 404

        # Get readings using detailed_reading view
        readings_list = dbmanager.getAllWhere('detailed_reading', 'patient_id = %s', patient_id)

        # Get notifications
        notifs_list = dbmanager.getAllWhere('notification', 'patient_id = %s', patient_id)

        # Create a Patient_Report object with patient info
        patient_report_data = {
            "id": patient_id,
            "first_name": getattr(patient_basic_info, 'first_name', ''),
            "last_name": getattr(patient_basic_info, 'last_name', ''),
            "age_group": getattr(patient_basic_info, 'age', 'Unknown'),
            "sex": getattr(patient_basic_info, 'sex', 'Unknown'),
            "hypertension": int(getattr(patient_basic_info, 'hypertension', 0)),
            "diabetes": int(getattr(patient_basic_info, 'diabetes', 0)),
            "smoking_history": int(getattr(patient_basic_info, 'smoking_history', 0))
        }

        # Process readings if they exist
        readings = []
        if readings_list:
            # Sort readings by timestamp (newest first)
            readings_list.sort(key=lambda x: getattr(x, 'timestamp', datetime.min), reverse=True)

            # Get the latest reading
            latest_reading = readings_list[0] if readings_list else None

            if latest_reading:
                # Add latest reading data to patient report
                patient_report_data.update({
                    "latest_reading_timestamp": getattr(latest_reading, 'timestamp', None),
                    "latest_reading_left_sensory_score": float(getattr(latest_reading, 'left_sensory_score', 0)),
                    "latest_reading_right_sensory_score": float(getattr(latest_reading, 'right_sensory_score', 0)),
                    "latest_reading_asymmetry_difference": float(getattr(latest_reading, 'asymmetry_difference', 0)),
                    "latest_reading_average_asymmetry": float(getattr(latest_reading, 'average_asymmetry', 0)),
                    "latest_reading_asymmetry_index": float(getattr(latest_reading, 'asymmetry_index', 0)),
                    "latest_reading_risk_label": getattr(latest_reading, 'risk_label', 'Normal'),
                })

            # Find the reading with highest asymmetry
            if readings_list:
                highest_reading = max(readings_list,
                                      key=lambda x: float(getattr(x, 'asymmetry_index', 0)))

                # Add highest reading data
                patient_report_data.update({
                    "highest_reading_timestamp": getattr(highest_reading, 'timestamp', None),
                    "highest_reading_left_sensory_score": float(getattr(highest_reading, 'left_sensory_score', 0)),
                    "highest_reading_right_sensory_score": float(getattr(highest_reading, 'right_sensory_score', 0)),
                    "highest_reading_asymmetry_difference": float(getattr(highest_reading, 'asymmetry_difference', 0)),
                    "highest_reading_average_asymmetry": float(getattr(highest_reading, 'average_asymmetry', 0)),
                    "highest_reading_asymmetry_index": float(getattr(highest_reading, 'asymmetry_index', 0)),
                    "highest_reading_risk_label": getattr(highest_reading, 'risk_label', 'Normal'),
                })

            # Calculate averages across all readings
            if readings_list:
                avg_left = sum(float(getattr(r, 'left_sensory_score', 0)) for r in readings_list) / len(readings_list)
                avg_right = sum(float(getattr(r, 'right_sensory_score', 0)) for r in readings_list) / len(readings_list)
                avg_asymmetry_diff = sum(float(getattr(r, 'asymmetry_difference', 0)) for r in readings_list) / len(readings_list)
                avg_avg_asymmetry = sum(float(getattr(r, 'average_asymmetry', 0)) for r in readings_list) / len(readings_list)
                avg_asymmetry_idx = sum(float(getattr(r, 'asymmetry_index', 0)) for r in readings_list) / len(readings_list)

                # Add average data
                patient_report_data.update({
                    "avg_left_sensory_score": round(avg_left, 2),
                    "avg_right_sensory_score": round(avg_right, 2),
                    "avg_asymmetry_difference": round(avg_asymmetry_diff, 2),
                    "avg_average_asymmetry": round(avg_avg_asymmetry, 2),
                    "avg_asymmetry_index": round(avg_asymmetry_idx, 4),
                })

            # Determine risk labels based on average
            if 'avg_asymmetry_index' in patient_report_data:
                avg_asymmetry = patient_report_data["avg_asymmetry_index"]

                if avg_asymmetry > 0.2:
                    avg_risk_label = 'Critical'
                elif avg_asymmetry > 0.15:
                    avg_risk_label = 'Borderline'
                else:
                    avg_risk_label = 'Normal'

                patient_report_data["avg_risk_label"] = avg_risk_label

            # Prepare readings for template (use existing risk_label from view)
            for reading in readings_list[:10]:  # Limit to 10 most recent
                readings.append(reading)

        else:
            # No readings yet
            patient_report_data.update({
                "latest_reading_timestamp": None,
                "latest_reading_left_sensory_score": 0,
                "latest_reading_right_sensory_score": 0,
                "latest_reading_asymmetry_difference": 0,
                "latest_reading_average_asymmetry": 0,
                "latest_reading_asymmetry_index": 0,
                "latest_reading_risk_label": "No readings",

                "highest_reading_timestamp": None,
                "highest_reading_left_sensory_score": 0,
                "highest_reading_right_sensory_score": 0,
                "highest_reading_asymmetry_difference": 0,
                "highest_reading_average_asymmetry": 0,
                "highest_reading_asymmetry_index": 0,
                "highest_reading_risk_label": "No readings",

                "avg_left_sensory_score": 0,
                "avg_right_sensory_score": 0,
                "avg_asymmetry_difference": 0,
                "avg_average_asymmetry": 0,
                "avg_asymmetry_index": 0,
                "avg_risk_label": "No readings",
            })

        # For doctors, get doctor info
        if user_role == 'DOCTOR':
            doctor_info = dbmanager.getByID('doctor_info', user_id)
            if doctor_info:
                patient_report_data.update({
                    "doctor_id": user_id,
                    "doctor_first_name": getattr(doctor_info, 'first_name', ''),
                    "doctor_last_name": getattr(doctor_info, 'last_name', ''),
                    "doctor_title": getattr(doctor_info, 'title', 'Dr.'),
                    "doctor_qualification": getattr(doctor_info, 'qualification', ''),
                    "doctor_profession": getattr(doctor_info, 'profession', ''),
                })

        # Create Patient_Report object
        from model.db.Patient_Report import Patient_Report
        patient_report = Patient_Report(**patient_report_data)

        return render_template('dashboard_patient.html',
                               patient=patient_report,
                               readings=readings,
                               notifs=notifs_list,
                               model_loaded=model is not None)

    except Exception as ex:
        import traceback
        traceback.print_exc()
        return render_template('error.html',
                               error=f"Error loading dashboard: {str(ex)}",
                               redirect_url="/"), 500

@app.route('/dashboard/patient')
def default_dashboard():
    """Redirect patient to their own dashboard"""
    if 'user_id' not in session:
        return redirect('/login')

    if session.get('role') == 'PATIENT':
        return redirect(f'/dashboard/patient/{session["user_id"]}')
    elif session.get('role') == 'DOCTOR':
        return redirect('/dashboard/doctor')
    else:
        return redirect('/login')


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