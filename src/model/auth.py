from flask import Blueprint, request, jsonify, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
import sys
import os

# Fix import path - database.py is in src/sample/
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sample'))

try:
    from database import get_connection
    print("✅ Successfully imported database functions from src/sample/")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Direct connection as fallback
    import mariadb

    def get_connection():
        return mariadb.connect(
            user="Lacunar",
            password="LacunarStroke1234",
            host="54.37.40.206",
            port=3306,
            database="lacunar_stroke"
        )

# Create Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    data = request.form

    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'patient')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    if role not in ['patient', 'doctor']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    try:
        # Check if user already exists
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM user WHERE email = %s', (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Hash password
        hashed_password = generate_password_hash(password)

        # Insert user
        cursor.execute(
            'INSERT INTO user (email, password, role) VALUES (%s, %s, %s)',
            (email, hashed_password, role)
        )

        user_id = cursor.lastrowid

        # If registering as patient, create patient_info entry
        if role == 'patient':
            cursor.execute(
                '''INSERT INTO patient_info (id, first_name, last_name)
                   VALUES (%s, %s, %s)''',
                (user_id, '', '')
            )

        conn.commit()
        cursor.close()
        conn.close()

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
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE email = %s', (email,))
        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Check password
        if 'password' not in user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'User record has no password field'}), 500

        if not check_password_hash(user['password'], password):
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Set session data
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user.get('role', 'patient')

        # Get patient info if role is patient
        if session['role'] == 'patient':
            cursor.execute('SELECT * FROM patient_info WHERE id = %s', (user['id'],))
            patient_info = cursor.fetchone()

            if patient_info:
                session['patient_name'] = f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}".strip()

        cursor.close()
        conn.close()

        # Redirect based on role
        if session['role'] == 'doctor':
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
    return redirect('/'_)