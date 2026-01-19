from flask import Blueprint, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import src.model.database as dbmanager
import sys
import os

from model.db.Patient_Info import Patient_Info
from model.db.User import User

# Fix import path - database.py is in src/sample/
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sample'))



# Create Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.form

    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'PATIENT')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    if role not in ['PATIENT', 'DOCTOR']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    try:
        # Check if user already exists
        if dbmanager.getWhere('user', 'email = ?', email):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Create user
        user = User(email=email, password=generate_password_hash(password), role=role)
        user_id = dbmanager.insert('user', user)

        # If registering as patient, create patient_info entry
        if role == 'PATIENT':
            patient = Patient_Info(id=user_id, first_name='', last_name='')
            patient.id = user_id
            dbmanager.insert('patient_info', patient)
        ## do as doctor after


        return jsonify({
            'success': True,
            'message': f'Registration successful as {role}',
            'redirect': '/login'
        }), 201

    except Exception as e:
        import traceback
        print(f"Registration error: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login"""
    data = request.form

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    try:
        # Get user
        user = dbmanager.getWhere('user', 'email = ?', email)

        if not user or not check_password_hash(user.password, password):
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Set session data
        session['user_id'] = user.id
        session['email'] = user.email
        session['role'] = user.role

        # Get patient info if role is patient
        if session['role'] == 'PATIENT':
            patient_info = dbmanager.getByID('patient_info', user.id)
            if patient_info:
                session['name'] = f"{patient_info.first_name} {patient_info.last_name}".strip()
        elif session['role'] == 'DOCTOR':
            doctor_info = dbmanager.getByID('doctor_info', user.id)
            if doctor_info:
                session['name'] = f"{doctor_info.first_name} {doctor_info.last_name}".strip()

        # Redirect based on role
        if session['role'] == 'DOCTOR':
            redirect_url = '/dashboard/doctor'
        else:
            redirect_url = '/dashboard/patient'

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': redirect_url,
            'role': session['role']
        })

    except Exception as e:
        import traceback
        print(f"Login error: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect('/')