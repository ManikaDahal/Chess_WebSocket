# WEBSOCKET-ONLY Django Project for Render Deployment
# This is a minimal Django project that ONLY handles WebSocket signaling
# All REST APIs are handled by the main project deployed on Vercel

import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-websocket-only-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    '.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',  
    'daphne',  # ASGI server for WebSocket support
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'channels',  # Django Channels for WebSocket
    'call',  # WebSocket consumer app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'websocket_project.urls'

TEMPLATES = []

# ASGI Application for WebSocket support
ASGI_APPLICATION = 'websocket_project.asgi.application'

# Channel Layers for WebSocket communication
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}

# Database - Not needed for WebSocket-only service
# Using SQLite as placeholder (won't be used)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS settings - Allow connections from your Flutter app and Vercel API
CORS_ALLOW_ALL_ORIGINS = True  # For development, restrict in production

# Logging for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
