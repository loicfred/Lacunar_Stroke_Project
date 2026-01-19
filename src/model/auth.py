from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

# Import from your existing database.py
try:
    from src.model.db.database import get_connection, insert, getAll, getByID
    print("✅ Successfully imported database functions")
except ImportError as e:
    print(f"❌ Import error: {e}")
    # Fallback to direct connection
    import mariadb
    from config import config

    def get_connection():
        return mariadb.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )

# Create Blueprint for authentication
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Handle user registration using existing database.py"""
    data = request.form

    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'patient')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    if role not in ['patient', 'doctor', 'admin']:
        return jsonify({'success': False, 'message': 'Invalid role'}), 400

    try:
        # Check if user already exists
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id FROM user WHERE email = ?', (email,))
        existing_user = cursor.fetchone()
        cursor.close()
        conn.close()

        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered'}), 400

        # Create user using User model
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, role=role)

        # Insert using existing database.py function
        user_id = insert("user", user)

        # If patient, create patient_info entry
        if role == 'patient':
            from src.model.Patient_Info import Patient_Info
            patient = Patient_Info(
                id=user_id,
                first_name='',
                last_name='',
                age_group='',
                sex='',
                hypertension=0,
                diabetes=0,
                smoking_history=0
            )
            insert("patient_info", patient)

        return jsonify({
            'success': True,
            'message': f'Registration successful as {role}',
            'redirect': '/login'
        }), 201

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Handle user login using existing database.py"""
    data = request.form

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required'}), 400

    try:
        # Get user using database connection
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM user WHERE email = ?', (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if not user:
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Check password
        if not check_password_hash(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        # Set session data
        session['user_id'] = user['id']
        session['email'] = user['email']
        session['role'] = user['role']

        # Get patient info if role is patient
        if user['role'] == 'patient':
            conn = get_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute('SELECT * FROM patient_info WHERE id = ?', (user['id'],))
            patient_info = cursor.fetchone()
            cursor.close()
            conn.close()

            if patient_info:
                session['patient_name'] = f"{patient_info.get('first_name', '')} {patient_info.get('last_name', '')}".strip()

        # Redirect based on role
        if user['role'] in ['admin', 'doctor']:
            redirect_url = '/dashboard/doctor'
        else:  # patient
            redirect_url = '/dashboard/patient'

        return jsonify({
            'success': True,
            'message': 'Login successful',
            'redirect': redirect_url,
            'role': user['role']
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@auth_bp.route('/logout')
def logout():
    """Handle user logout"""
    session.clear()
    return redirect(url_for('index'))

@auth_bp.route('/api/current-user')
def get_current_user():
    """Get current user info"""
    if 'user_id' not in session:
        return jsonify({'authenticated': False}), 401

    return jsonify({
        'authenticated': True,
        'user_id': session['user_id'],
        'email': session['email'],
        'role': session['role'],
        'patient_name': session.get('patient_name', '')
    })