import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ai_search'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_POOL_SIZE = 10
SQLALCHEMY_MAX_OVERFLOW = 20

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

# Content filtering configuration
CONTENT_FILTER = {
    'min_length': 3,
    'max_length': 100,
    'profanity_check': True,
    'sentiment_analysis': True
}

# AI model configuration
MODEL_CONFIG = {
    'model_path': 'models/trained/',
    'vectorizer_path': 'models/vectorizer/',
    'min_prediction_confidence': 0.7,
    'max_suggestions': 5
}

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': os.getenv('REDIS_HOST', 'localhost'),
    'CACHE_REDIS_PORT': int(os.getenv('REDIS_PORT', 6379)),
    'CACHE_DEFAULT_TIMEOUT': 300
}

# API rate limiting
RATELIMIT_DEFAULT = "100/hour"
RATELIMIT_STORAGE_URL = "redis://localhost:6379/0"

# CORS configuration
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# Logging configuration
LOG_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/app.log',
            'maxBytes': 1024 * 1024,
            'backupCount': 5,
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['file']
    }
}
