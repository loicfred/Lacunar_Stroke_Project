"""
Configuration for Lacunar Stroke Detection System
Green: Centralized configuration for all team modules
Version: 1.0.0
"""

import os
from pathlib import Path
from typing import Dict, Any

# ========== PROJECT ROOT & PATHS ==========
BASE_DIR = Path(__file__).resolve().parent
print(f"📍 Project root: {BASE_DIR}")

# Core directories (must exist)
SRC_DIR = BASE_DIR / "src"
WEB_DIR = SRC_DIR / "web"
TEMPLATES_DIR = BASE_DIR / "templates"
DATA_SIM_DIR = SRC_DIR / "data_simulation" / "master_data"
AI_MODELS_DIR = SRC_DIR / "ai_models"
MODEL_DIR = SRC_DIR / "model"
TESTS_DIR = BASE_DIR / "tests"

# Optional directories (will be created)
MODELS_STORAGE_DIR = BASE_DIR / "models"  # For trained model files
STATIC_DIR = BASE_DIR / "static"          # For CSS/JS files
LOGS_DIR = BASE_DIR / "logs"              # For application logs
DOCS_DIR = BASE_DIR / "docs"              # For documentation

# Create optional directories
for dir_path in [MODELS_STORAGE_DIR, STATIC_DIR, LOGS_DIR, DOCS_DIR]:
    dir_path.mkdir(exist_ok=True)

# ========== FLASK APPLICATION CONFIG ==========
class FlaskConfig:
    """Flask application configuration"""
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'lacunar-stroke-dev-key-2024-change-me')
    
    # Application settings
    DEBUG = True
    TESTING = False
    PROPAGATE_EXCEPTIONS = True
    
    # Paths
    TEMPLATE_FOLDER = str(TEMPLATES_DIR)
    STATIC_FOLDER = str(STATIC_DIR)
    STATIC_URL_PATH = '/static'
    
    # JSON settings
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    JSONIFY_MIMETYPE = 'application/json'
    
    # Server settings
    HOST = '0.0.0.0'
    PORT = 5000
    RELOAD = True
    
    # Request handling
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    TRAP_HTTP_EXCEPTIONS = True

# ========== MODEL CONFIGURATION ==========
MODEL_CONFIG: Dict[str, Any] = {
    # Current simple threshold model
    'asymmetry_threshold': 2.0,
    'min_sensory_score': 3.0,
    'max_sensory_score': 10.0,
    'confidence_base': 0.5,
    'confidence_max': 0.95,
    'confidence_scale': 10.0,
    
    # Sensory simulation
    'sensory_simulation': {
        'healthy_base_range': (7.0, 10.0),
        'bilateral_deficit_range': (1.0, 4.5),
        'unilateral_deficit_range': (1.5, 5.0),
        'asymmetric_probability': 0.4,
        'bilateral_probability': 0.1,
        'normal_variation': (-0.3, 0.3)
    },
    
    # response_strength thresholds
    'response_strength_levels': {
        'mild_threshold': 2.5,
        'moderate_threshold': 4.0,
        'severe_label': "Severe"
    }
}

# ========== PATIENT DATA CONFIG ==========
PATIENT_CONFIG: Dict[str, Any] = {
    # Demographics
    'demographics': {
        'age_groups': ["40-49", "50-59", "60-69", "70-79"],
        'sex_options': ["Male", "Female"],
        'conditions': ["hypertension", "diabetes", "smoking_history"],
        'condition_values': [0, 1]
    },
    
    # Generation limits
    'generation': {
        'default_sample_size': 5,
        'max_api_generation': 100,
        'max_simulation': 1000,
        'api_response_limit': 20,
        'dashboard_display': 5
    }
}

# ========== API CONFIGURATION ==========
API_CONFIG: Dict[str, Any] = {
    'endpoints': {
        'home': '/',
        'get_patients': '/api/patients',
        'predict': '/api/predict',
        'dashboard': '/api/dashboard',
        'clear': '/api/clear',
        'generate': '/api/generate-new/<int:amount>',
        'status': '/status'
    }
}

# ========== TEAM MODULE STATUS ==========
def check_module_status() -> Dict[str, Dict[str, bool]]:
    """Check which team modules are available"""
    return {
        'GREEN': {
            'flask_app': (WEB_DIR / "app.py").exists(),
            'templates': TEMPLATES_DIR.exists(),
            'config': True
        },
        'BLUE': {
            'patient_generator': (DATA_SIM_DIR / "patient_generator.py").exists(),
            'sensory_simulator': (DATA_SIM_DIR / "sensory_simulator.py").exists(),
            'random_forest_model': (AI_MODELS_DIR / "random_forest_model.py").exists(),
            'rnn_model': (AI_MODELS_DIR / "rnn_model.py").exists(),
            'patient_model': (MODEL_DIR / "Patient.py").exists()
        },
        'RED': {
            'api_endpoints': True,
            'error_handlers': True
        },
        'PURPLE': {
            'dashboard': (WEB_DIR / "dashboard.py").exists(),
            'tests': TESTS_DIR.exists() and len(list(TESTS_DIR.glob("*.py"))) > 0,
            'documentation': DOCS_DIR.exists()
        }
    }

TEAM_MODULES = check_module_status()

# ========== ENVIRONMENT CONFIG ==========
ENV = os.environ.get('FLASK_ENV', 'development').lower()

if ENV == 'production':
    FlaskConfig.DEBUG = False
    FlaskConfig.SECRET_KEY = os.environ.get('SECRET_KEY', os.urandom(24))
elif ENV == 'testing':
    FlaskConfig.DEBUG = False
    FlaskConfig.TESTING = True
    MODEL_CONFIG['asymmetry_threshold'] = 1.5

# ========== CONFIGURATION VALIDATION ==========
if __name__ == '__main__':
    print("\n" + "="*70)
    print("LACUNAR STROKE DETECTION SYSTEM - CONFIGURATION")
    print("="*70)
    
    print(f"\n📋 Environment: {ENV.upper()}")
    print(f"📍 Project Root: {BASE_DIR}")
    
    print(f"\n📁 Directory Status:")
    dirs_to_check = {
        'Source': SRC_DIR,
        'Web App': WEB_DIR,
        'Data Simulation': DATA_SIM_DIR,
        'AI Models': AI_MODELS_DIR,
        'Models Storage': MODELS_STORAGE_DIR,
        'Static Files': STATIC_DIR
    }
    
    for name, path in dirs_to_check.items():
        status = "✅" if path.exists() else "❌"
        print(f"  {status} {name}: {path}")
    
    print(f"\n👥 Team Module Status:")
    for team, modules in TEAM_MODULES.items():
        available = sum(modules.values())
        total = len(modules)
        percentage = (available / total * 100) if total > 0 else 0
        status_icon = "✅" if percentage > 75 else "⚠️" if percentage > 50 else "❌"
        print(f"  {status_icon} {team}: {available}/{total} ({percentage:.0f}%)")
    
    print(f"\n⚙️  Model Configuration:")
    print(f"  • Asymmetry Threshold: {MODEL_CONFIG['asymmetry_threshold']}")
    
    print(f"\n👤 Patient Configuration:")
    print(f"  • Age Groups: {', '.join(PATIENT_CONFIG['demographics']['age_groups'])}")
    
    print(f"\n🌐 API Endpoints:")
    for name, endpoint in API_CONFIG['endpoints'].items():
        print(f"  • {name}: {endpoint}")
    
    print(f"\n✅ Configuration loaded successfully!")
    print("="*70)