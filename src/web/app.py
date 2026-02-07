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
        # Use the database function that already calculates volatility
        volatility = dbmanager.calculate_volatility_index(patient_id)

        # If no volatility from database, calculate it manually
        if volatility == 0.0:
            history = dbmanager.get_recent_readings(patient_id, limit=4)
            if not history or len(history) < 2:
                return 0.0

            # Take the last 4 readings from DB + the current score
            recent_scores = []
            for r in history[:4]:
                # Handle both dictionary and object formats
                if isinstance(r, dict):
                    left = float(r.get('left_sensory_score', 0))
                    right = float(r.get('right_sensory_score', 0))
                else:
                    # It's an object
                    left = float(getattr(r, 'left_sensory_score', 0))
                    right = float(getattr(r, 'right_sensory_score', 0))

                recent_scores.append((left + right) / 2)

            recent_scores.append(current_avg_score)
            return float(np.std(recent_scores))

        return volatility

    except Exception as e:
        print(f"Error calculating stuttering volatility: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


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

def encode_bp_medication(bp_med_status):
    """Encode BP medication status to numerical values"""
    if isinstance(bp_med_status, str):
        encoding = {
            "No": 0,
            "Yes": 1,
            "Irregular": 2,
            "0": 0,
            "1": 1,
            "2": 2
        }
        return encoding.get(bp_med_status, 0)
    else:
        # If it's already a number, ensure it's 0, 1, or 2
        return int(bp_med_status) if bp_med_status in [0, 1, 2] else 0

# Add this helper function to app.py (near other helper functions)
def extract_pattern_features(reading_sequence):
    """
    Extract lacunar stroke pattern features from a sequence of readings.
    Same function as in patient_generator.py, added here for prediction.
    """
    if len(reading_sequence) < 2:
        return {}

    try:
        import numpy as np

        # Extract sensory scores from sequence
        left_scores = []
        right_scores = []
        for r in reading_sequence:
            if hasattr(r, 'left_sensory_score'):
                left_scores.append(float(r.left_sensory_score))
                right_scores.append(float(r.right_sensory_score))
            elif isinstance(r, dict):
                left_scores.append(float(r.get('left_sensory_score', 9.0)))
                right_scores.append(float(r.get('right_sensory_score', 9.0)))

        # Use the worse side for pattern analysis
        avg_scores = [(l + r) / 2 for l, r in zip(left_scores, right_scores)]

        # Calculate features
        volatility = float(np.std(avg_scores)) if len(avg_scores) > 1 else 0.0

        if len(avg_scores) >= 2:
            time_points = list(range(len(avg_scores)))
            slope, _ = np.polyfit(time_points, avg_scores, 1)
            velocity_trend = float(slope)
        else:
            velocity_trend = 0.0

        # Stuttering Score
        direction_changes = 0
        if len(avg_scores) >= 3:
            for i in range(1, len(avg_scores) - 1):
                prev = avg_scores[i-1]
                curr = avg_scores[i]
                nxt = avg_scores[i+1]
                if (curr > prev and curr > nxt) or (curr < prev and curr < nxt):
                    direction_changes += 1

        pattern_amplitude = max(avg_scores) - min(avg_scores) if avg_scores else 0.0

        return {
            'volatility_index': round(volatility, 3),
            'velocity_trend': round(velocity_trend, 4),
            'stuttering_score': direction_changes,
            'pattern_amplitude': round(pattern_amplitude, 3),
            'reading_count': len(reading_sequence)
        }

    except Exception as e:
        print(f"⚠️ Error extracting pattern features: {e}")
        return {}


def predict_with_model(patient_data):
    if model is None:
        return None

    try:
        # DEBUG: Print what we received
        print(f"\n🎯 DEBUG predict_with_model received:")
        for key, value in patient_data.items():
            print(f"  {key}: {value}")

        # 1. Prepare Basic Features - use values from patient_data
        left = float(patient_data.get("left_sensory_score", 9.0))
        right = float(patient_data.get("right_sensory_score", 9.0))

        # Calculate avg early to avoid UnboundLocalError
        avg = (left + right) / 2

        # Use form values if provided, otherwise calculate
        if "asymmetry_index" in patient_data:
            asymmetry_index = float(patient_data.get("asymmetry_index", 0.0))
        else:
            asymmetry_index = abs(left - right) / (avg + 1)

        # Use form values for pattern features
        pattern_volatility = float(patient_data.get("pattern_volatility", 0.0))
        pattern_velocity_trend = float(patient_data.get("pattern_velocity_trend", 0.0))
        pattern_stuttering_score = int(patient_data.get("pattern_stuttering_score", 0))
        pattern_amplitude = float(patient_data.get("pattern_amplitude", 0.0))
        pattern_asymmetry_progression = float(patient_data.get("pattern_asymmetry_progression", 0.0))
        pattern_type = int(patient_data.get("pattern_type", 0))
        pattern_consistency = float(patient_data.get("pattern_consistency", 0.0))
        pattern_reading_count = int(patient_data.get("pattern_reading_count", 5))

        # Use form values for other features
        score_velocity = float(patient_data.get("score_velocity", 0.0))
        volatility_index = float(patient_data.get("volatility_index", 0.0))

        # 2. Get Historical Data for Pattern Analysis
        patient_id = patient_data.get("id", 0)

        # Fetch Velocity from Database
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(patient_id)

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

        # 3. Get Recent Readings for Pattern Analysis
        recent_readings = dbmanager.get_recent_readings(patient_id, limit=5)

        # Calculate volatility from recent readings
        volatility = calculate_stuttering_volatility(patient_id, avg)

        # 4. Extract Pattern Features if we have enough historical data
        pattern_features = {}
        has_pattern_data = False

        if len(recent_readings) >= 3:
            try:
                # Create a reading sequence including current reading
                reading_sequence = []

                # Add historical readings
                for r in recent_readings:
                    # Create a simple SensoryDetails-like object
                    class ReadingWrapper:
                        def __init__(self, reading_dict):
                            self.left_sensory_score = float(reading_dict.get('left_sensory_score', 9.0))
                            self.right_sensory_score = float(reading_dict.get('right_sensory_score', 9.0))
                            self.asymmetry_index = reading_dict.get('asymmetry_index')
                            if self.asymmetry_index is None:
                                avg_score = (self.left_sensory_score + self.right_sensory_score) / 2
                                self.asymmetry_index = abs(self.left_sensory_score - self.right_sensory_score) / (avg_score + 1)

                    reading_sequence.append(ReadingWrapper(r))

                # Add current reading
                class CurrentReadingWrapper:
                    def __init__(self, left, right):
                        self.left_sensory_score = left
                        self.right_sensory_score = right
                        avg_score = (left + right) / 2
                        self.asymmetry_index = abs(left - right) / (avg_score + 1)

                reading_sequence.append(CurrentReadingWrapper(left, right))

                # Extract pattern features using the same logic as in patient_generator
                if len(reading_sequence) >= 3:
                    # Extract scores
                    left_scores = [r.left_sensory_score for r in reading_sequence]
                    right_scores = [r.right_sensory_score for r in reading_sequence]
                    avg_scores = [(l + r) / 2 for l, r in zip(left_scores, right_scores)]

                    # Calculate pattern features
                    pattern_volatility = float(np.std(avg_scores)) if len(avg_scores) > 1 else 0.0

                    # Velocity trend
                    if len(avg_scores) >= 2:
                        time_points = list(range(len(avg_scores)))
                        slope, _ = np.polyfit(time_points, avg_scores, 1)
                        pattern_velocity_trend = float(slope)
                    else:
                        pattern_velocity_trend = 0.0

                    # Stuttering score
                    direction_changes = 0
                    if len(avg_scores) >= 3:
                        for i in range(1, len(avg_scores) - 1):
                            prev = avg_scores[i-1]
                            curr = avg_scores[i]
                            nxt = avg_scores[i+1]
                            if (curr > prev and curr > nxt) or (curr < prev and curr < nxt):
                                direction_changes += 1

                    # Pattern amplitude
                    pattern_amplitude = max(avg_scores) - min(avg_scores) if avg_scores else 0.0

                    # Asymmetry progression
                    asymmetry_values = [r.asymmetry_index for r in reading_sequence]
                    if len(asymmetry_values) >= 2:
                        asym_slope, _ = np.polyfit(range(len(asymmetry_values)), asymmetry_values, 1)
                        asymmetry_progression = float(asym_slope)
                    else:
                        asymmetry_progression = 0.0

                    # Consistency score
                    if len(left_scores) >= 2 and len(right_scores) >= 2:
                        left_var = np.var(left_scores)
                        right_var = np.var(right_scores)
                        consistency = 1.0 - (abs(left_var - right_var) / max(left_var, right_var, 0.001))
                    else:
                        consistency = 1.0

                    pattern_features = {
                        'pattern_volatility_index': round(pattern_volatility, 3),
                        'pattern_velocity_trend': round(pattern_velocity_trend, 4),
                        'pattern_stuttering_score': direction_changes,
                        'pattern_pattern_amplitude': round(pattern_amplitude, 3),
                        'pattern_asymmetry_progression': round(asymmetry_progression, 4),
                        'pattern_consistency_score': round(consistency, 3)
                    }

                    has_pattern_data = True
                    print(f"🔍 Pattern features extracted: {pattern_features}")

            except Exception as pattern_error:
                print(f"⚠️ Error extracting pattern features: {pattern_error}")
                has_pattern_data = False

        # 5. Get all required features from patient_data
        sbp = float(patient_data.get("systolic_bp", 120))
        dbp = float(patient_data.get("diastolic_bp", 80))
        hba1c = float(patient_data.get("hba1c", 5.4))
        blood_glucose = float(patient_data.get("blood_glucose", 100))
        diabetes_type = patient_data.get("diabetes_type", "None")
        bp_category = patient_data.get("bp_category", "Normal")
        sm = int(patient_data.get("smoking_history", patient_data.get("smoking", 0)))

        # Encode categorical variables
        diabetes_type_encoded = encode_diabetes_type(diabetes_type)
        bp_category_encoded = encode_bp_category(bp_category)
        on_bp_medication = encode_bp_medication(patient_data.get("on_bp_medication", 0))
        # 6. Create input data with ALL expected features
        input_dict = {
            'left_sensory_score': left,
            'right_sensory_score': right,
            'asymmetry_index': asymmetry_index,
            'systolic_bp': sbp,
            'diastolic_bp': dbp,
            'hba1c': hba1c,
            'blood_glucose': blood_glucose,
            'diabetes_type': diabetes_type_encoded,
            'bp_category': bp_category_encoded,
            'on_bp_medication': on_bp_medication,
            'smoking_history': sm,
            'score_velocity': score_velocity,
            'volatility_index': volatility
        }

        # Add pattern features if available
        if has_pattern_data:
            for key, value in pattern_features.items():
                input_dict[key] = value

        # 7. Check what features the model expects
        model_features = []
        if hasattr(model, 'feature_names_in_'):
            model_features = list(model.feature_names_in_)
            print(f"📋 Model expects {len(model_features)} features: {model_features[:5]}...")
        else:
            # Use all features we have
            model_features = list(input_dict.keys())

        # 8. Create input data with only the features the model expects
        input_values = []
        for feat in model_features:
            if feat in input_dict:
                input_values.append(input_dict[feat])
            else:
                # If model expects a feature we don't have, use 0
                print(f"⚠️  Feature '{feat}' expected by model but not in input data, using 0")
                input_values.append(0)

        input_data = pd.DataFrame([input_values], columns=model_features)

        # Debug: Show what we're sending to the model
        print(f"🔍 Input data shape: {input_data.shape}")
        print(f"🔍 Features sent: {list(input_data.columns)}")

        # 9. Get Prediction and Probabilities
        prediction_code = int(model.predict(input_data)[0])
        probs = model.predict_proba(input_data)[0]
        confidence = max(probs)

        print(f"🔍 Prediction: Tier {prediction_code}, Confidence: {confidence:.2%}")

        # 10. Post-processing rules with pattern consideration
        # Override to bilateral if pattern shows high stuttering AND negative velocity
        if has_pattern_data:
            pattern_stuttering = pattern_features.get('pattern_stuttering_score', 0)
            pattern_volatility_val = pattern_features.get('pattern_volatility_index', 0)

            # Lacunar stroke pattern: high stuttering + high volatility + negative trend
            if pattern_stuttering >= 3 and pattern_volatility_val > 1.5 and score_velocity < -0.005:
                prediction_code = max(prediction_code, 3)  # At least severe unilateral
                print(f"🔍 Lacunar pattern detected: stuttering={pattern_stuttering}, volatility={pattern_volatility_val}")

        # Additional override for high volatility and negative velocity
        if volatility > 1.2 and score_velocity < -0.8:
            prediction_code = 4
            print(f"🔍 Override to bilateral due to high volatility ({volatility}) and negative velocity ({score_velocity})")

        # 11. Determine Affected Side & Bilateral Risk with pattern consideration
        if prediction_code == 4 or (left < 6.0 and right < 6.0):
            affected_side = "Bilateral (Both Sides)"
            # Check if it's truly bilateral or just severe unilateral
            if has_pattern_data and pattern_features.get('pattern_asymmetry_progression', 0) > 0.01:
                # Asymmetry is increasing - likely unilateral getting worse
                if left < right - 1.0:
                    affected_side = "Left (Severe)"
                elif right < left - 1.0:
                    affected_side = "Right (Severe)"
        elif left < right - 0.5:
            affected_side = "Left"
        elif right < left - 0.5:
            affected_side = "Right"
        else:
            affected_side = "None"

        # 12. Clinical Label Mapping
        impact_labels = {
            0: {"label": "Strong Response", "level": "low", "emoji": "🟢"},
            1: {"label": "Slightly Reduced", "level": "medium", "emoji": "🟡"},
            2: {"label": "Moderately Reduced", "level": "medium", "emoji": "🟠"},
            3: {"label": "Significantly Reduced", "level": "high", "emoji": "🔴"},
            4: {"label": "Weak Global Response", "level": "critical", "emoji": "🟣"}
        }

        res = impact_labels.get(prediction_code, impact_labels[0])

        # 13. Cliff-Edge Smoothing with pattern confidence
        display_label = res["label"]

        # Adjust confidence based on pattern data availability
        pattern_confidence_factor = 1.0
        if has_pattern_data:
            pattern_confidence_factor = 1.2  # More confident with pattern data
            # Add pattern qualifier for lacunar strokes
            if pattern_features.get('pattern_stuttering_score', 0) >= 3:
                display_label = f"Lacunar Pattern: {display_label}"

        adjusted_confidence = confidence * pattern_confidence_factor

        if adjusted_confidence < 0.55:
            display_label = f"Borderline {display_label}"
            print(f"🔍 Borderline flag added (confidence: {adjusted_confidence:.2%})")

        # Add confidence-based qualifier
        if adjusted_confidence < 0.4:
            display_label = f"Low Confidence: {display_label}"
            print(f"🔍 Low confidence flag added (confidence: {adjusted_confidence:.2%})")

        # 14. Pattern Analysis Summary
        pattern_analysis = None
        if has_pattern_data:
            pattern_stuttering_level = "stable"
            stuttering_score = pattern_features.get('pattern_stuttering_score', 0)
            if stuttering_score >= 3:
                pattern_stuttering_level = "HIGH stuttering (Lacunar pattern)"
            elif stuttering_score >= 2:
                pattern_stuttering_level = "moderate stuttering"
            elif stuttering_score >= 1:
                pattern_stuttering_level = "mild stuttering"

            pattern_analysis = {
                'stuttering_level': pattern_stuttering_level,
                'stuttering_score': stuttering_score,
                'volatility': pattern_features.get('pattern_volatility_index', 0),
                'trend': pattern_features.get('pattern_velocity_trend', 0),
                'amplitude': pattern_features.get('pattern_pattern_amplitude', 0),
                'readings_used': len(recent_readings) + 1
            }

        return {
            "prediction_code": prediction_code,
            "sensory_response": display_label,
            "risk_level": res["level"],
            "state_emoji": res["emoji"],
            "affected_side": affected_side,
            "model_confidence": round(confidence, 3),
            "adjusted_confidence": round(adjusted_confidence, 3),
            "asymmetry_index": round(asymmetry_index, 3),
            "volatility": round(volatility, 3),
            "score_velocity": score_velocity,
            "has_pattern_data": has_pattern_data,
            "pattern_analysis": pattern_analysis,
            "features_used": len(model_features),
            "pattern_features_count": len(pattern_features) if has_pattern_data else 0
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

    role = session['role']

    if role != 'PATIENT':
        if role == 'DOCTOR':
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

        # 3. Input Extraction and Validation - FIXED FIELD NAMES
        try:
            # CRITICAL: Use correct field names from predict_form.html
            left_score = float(request.form.get("left_sensory_score", 9.0))
            right_score = float(request.form.get("right_sensory_score", 9.0))
            asymmetry_index = float(request.form.get("asymmetry_index", 0.0))
            score_velocity = float(request.form.get("score_velocity", 0.0))
            volatility_index = float(request.form.get("volatility_index", 0.0))
            pattern_volatility = float(request.form.get("pattern_volatility", 0.0))
            pattern_velocity_trend = float(request.form.get("pattern_velocity_trend", 0.0))
            pattern_stuttering_score = int(request.form.get("pattern_stuttering_score", 0))
            pattern_amplitude = float(request.form.get("pattern_amplitude", 0.0))
            pattern_asymmetry_progression = float(request.form.get("pattern_asymmetry_progression", 0.0))
            pattern_type = int(request.form.get("pattern_type", 0))
            pattern_consistency = float(request.form.get("pattern_consistency", 0.0))
            pattern_reading_count = int(request.form.get("pattern_reading_count", 5))

            # Ensure scores are within clinical bounds (0.0 to 10.0)
            if not (0 <= left_score <= 10 and 0 <= right_score <= 10):
                raise ValueError("Sensory scores must be between 0 and 10.")

            # Get all required fields with fallbacks - FIXED FIELD NAMES
            sbp = float(request.form.get("systolic_bp") or getattr(patient_info, 'systolic_bp', 120))
            dbp = float(request.form.get("diastolic_bp") or getattr(patient_info, 'diastolic_bp', 80))
            hba1c = float(request.form.get("hba1c") or getattr(patient_info, 'hba1c', 5.4))
            blood_glucose = float(request.form.get("blood_glucose") or getattr(patient_info, 'blood_glucose', 100))

            # CRITICAL: Get smoking from correct field name
            smoking_history = int(request.form.get("smoking_history") or getattr(patient_info, 'smoking_history', 0))

            # Categorical fields
            diabetes_type = request.form.get("diabetes_type") or getattr(patient_info, 'diabetes_type', 'None')
            bp_category = request.form.get("bp_category") or getattr(patient_info, 'bp_category', 'Normal')
            on_bp_medication = int(request.form.get("bp_medication") or getattr(patient_info, 'on_bp_medication', 0))

            # Validate ranges
            if not (60 <= dbp <= 130):
                raise ValueError("Diastolic BP must be between 60 and 130 mmHg")
            if not (70 <= blood_glucose <= 500):
                raise ValueError("Blood glucose must be between 70 and 500 mg/dL")

        except ValueError as ve:
            logging.error(f"Validation Error: {ve}")
            return render_template('error.html', error=f"Invalid input data: {str(ve)}"), 400

        # 4. Calculate temporal features (optional, can use form values instead)
        l_vel, r_vel, t_delta = dbmanager.get_reading_velocity(user_id)
        current_velocity = min(l_vel, r_vel) if (l_vel is not None and r_vel is not None) else 0.0

        avg_score = (left_score + right_score) / 2
        volatility = calculate_stuttering_volatility(user_id, avg_score)

        # 5. Prediction Logic - UPDATED with all 21 features
        patient_dict = {
            "id": user_id,  # Add patient_id for historical data lookup
            "left_sensory_score": left_score,
            "right_sensory_score": right_score,
            "asymmetry_index": asymmetry_index,
            "systolic_bp": sbp,
            "diastolic_bp": dbp,
            "hba1c": hba1c,
            "blood_glucose": blood_glucose,
            "diabetes_type": diabetes_type,
            "bp_category": bp_category,
            "on_bp_medication": on_bp_medication,
            "smoking_history": smoking_history,
            "score_velocity": score_velocity,
            "volatility_index": volatility_index,
            # Pattern features
            "pattern_volatility": pattern_volatility,
            "pattern_velocity_trend": pattern_velocity_trend,
            "pattern_stuttering_score": pattern_stuttering_score,
            "pattern_amplitude": pattern_amplitude,
            "pattern_asymmetry_progression": pattern_asymmetry_progression,
            "pattern_type": pattern_type,
            "pattern_consistency": pattern_consistency,
            "pattern_reading_count": pattern_reading_count
        }

        # 6. Debug: Print what we received
        print(f"\n📋 DEBUG - Form data received:")
        for key, value in patient_dict.items():
            print(f"  {key}: {value}")

        # Attempt ML Prediction
        prediction = None
        if model:
            try:
                prediction = predict_with_model(patient_dict)
                print(f"✅ ML Prediction successful: {prediction}")
            except Exception as e:
                logging.error(f"ML Prediction failed, falling back: {e}")
                import traceback
                traceback.print_exc()

        if not prediction:
            print("⚠️ Using threshold fallback prediction")
            prediction = predict_stroke_threshold(patient_dict)

        # 7. Database Persistence - WITH ROBUST ERROR HANDLING
        try:
            # First, try to check what columns exist in the reading table
            import mariadb

            try:
                conn = mariadb.connect(
                    user="Lacunar",
                    password="LacunarStroke1234",
                    host="54.37.40.206",
                    port=3306,
                    database="lacunar_stroke"
                )
                cursor = conn.cursor()

                # Check what columns exist in reading table
                cursor.execute("SHOW COLUMNS FROM reading")
                existing_columns = [col[0] for col in cursor.fetchall()]
                conn.close()

                print(f"📊 Existing columns in reading table: {len(existing_columns)}")

                # Prepare data for insertion based on what columns exist
                reading_data = {
                    'patient_id': user_id,
                    'timestamp': datetime.now(),
                    'left_sensory_score': left_score,
                    'right_sensory_score': right_score,
                    'systolic_bp': sbp,
                    'diastolic_bp': dbp,
                    'hba1c': hba1c,
                    'blood_glucose': blood_glucose,
                    'diabetes_type': diabetes_type,
                    'bp_category': bp_category,
                    'on_bp_medication': on_bp_medication
                }

                # Add pattern features only if columns exist
                pattern_fields = {
                    'asymmetry_index': asymmetry_index,
                    'score_velocity': score_velocity,
                    'volatility_index': volatility_index,
                    'pattern_volatility': pattern_volatility,
                    'pattern_velocity_trend': pattern_velocity_trend,
                    'pattern_stuttering_score': pattern_stuttering_score,
                    'pattern_amplitude': pattern_amplitude,
                    'pattern_asymmetry_progression': pattern_asymmetry_progression,
                    'pattern_type': pattern_type,
                    'pattern_consistency': pattern_consistency,
                    'pattern_reading_count': pattern_reading_count
                }

                for field_name, field_value in pattern_fields.items():
                    if field_name in existing_columns:
                        reading_data[field_name] = field_value
                    else:
                        print(f"⚠️ Column '{field_name}' not in reading table, skipping")

                # Add prediction results if columns exist
                if prediction:
                    prediction_fields = {
                        'prediction_tier': prediction.get('prediction_code'),
                        'risk_label': prediction.get('sensory_response'),
                        'affected_side': prediction.get('affected_side'),
                        'model_confidence': prediction.get('model_confidence')
                    }

                    for field_name, field_value in prediction_fields.items():
                        if field_name in existing_columns:
                            reading_data[field_name] = field_value

                # Insert using dbmanager with filtered data
                from model.db.Reading import Reading
                reading = Reading(**reading_data)

                try:
                    dbmanager.insert('reading', reading)
                    print(f"✅ Reading saved successfully with {len(reading_data)} fields")
                except Exception as insert_error:
                    print(f"⚠️ Could not save with dbmanager: {insert_error}")

                    # Fallback: Try direct SQL with minimal fields
                    try:
                        conn = mariadb.connect(
                            user="Lacunar",
                            password="LacunarStroke1234",
                            host="54.37.40.206",
                            port=3306,
                            database="lacunar_stroke"
                        )
                        cursor = conn.cursor()

                        # Build minimal insert query
                        minimal_fields = ['patient_id', 'left_sensory_score', 'right_sensory_score',
                                          'systolic_bp', 'diastolic_bp']
                        minimal_values = [user_id, left_score, right_score, sbp, dbp]

                        # Add timestamp if column exists
                        if 'timestamp' in existing_columns:
                            minimal_fields.append('timestamp')
                            minimal_values.append(datetime.now())

                        query = f"""
                            INSERT INTO reading ({', '.join(minimal_fields)})
                            VALUES ({', '.join(['%s'] * len(minimal_values))})
                        """

                        cursor.execute(query, tuple(minimal_values))
                        conn.commit()
                        conn.close()
                        print(f"✅ Reading saved with minimal fields: {minimal_fields}")

                    except Exception as sql_error:
                        print(f"❌ Could not save even minimal data: {sql_error}")
                        # Don't crash the app over database issues

            except Exception as db_check_error:
                print(f"⚠️ Could not check database structure: {db_check_error}")
                # Continue without saving to database

        except Exception as db_err:
            logging.error(f"Failed to save reading to database: {db_err}")
            import traceback
            traceback.print_exc()
            # We continue even if saving fails so the user gets their immediate result

        # 8. Prepare result data for template
        result_data = {
            "prediction": prediction,
            "timestamp": datetime.now(),
            "patient_data": {
                "scores": {"left": left_score, "right": right_score},
                "bp": {"systolic": sbp, "diastolic": dbp},
                "glucose": {"hba1c": hba1c, "blood_glucose": blood_glucose},
                "conditions": {
                    "diabetes_type": diabetes_type,
                    "bp_category": bp_category,
                    "on_bp_medication": on_bp_medication,
                    "smoking_history": smoking_history
                }
            },
            "pattern_features": {
                "volatility": pattern_volatility,
                "stuttering_score": pattern_stuttering_score,
                "pattern_type": pattern_type,
                "amplitude": pattern_amplitude
            }
        }

        # 9. Render result template
        return render_template('result.html',
                               data=result_data,
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
        if session['role'] != 'PATIENT': return redirect('/dashboard/doctor')

        return redirect(f'/dashboard/patient/{session['user_id']}')
    except Exception as ex:
        print(f"Patient dashboard error: {ex}")
        return render_template('error.html', error=str(ex))

@app.route('/dashboard/patient/<string:patient_id>')
def dashboard_patient(patient_id):
    try:
        if 'user_id' not in session: return redirect('/login')
        print(str(session['role']))
        if session['role'] == 'PATIENT' and str(session['user_id']) != str(patient_id):
            return render_template('error.html', error="You don't have permission to view this dashboard.",  redirect_url="/dashboard/patient"), 403

        patient_info = dbmanager.getByID('patient_report', patient_id)
        readings = dbmanager.getAllWhere('detailed_reading', 'patient_id = ? ORDER BY timestamp DESC', patient_id)
        notifs = dbmanager.getAllWhere('notification', 'patient_id = ?', patient_id)
        return render_template('dashboard_patient.html',patient=patient_info, readings=readings, notifs=notifs,model_loaded=model is not None)
    except Exception as ex:
        print(f"Patient dashboard error: {ex}")
        return render_template('error.html', error=str(ex))

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