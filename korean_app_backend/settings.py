"""
Django settings for korean_app_backend project.
"""

import sys
from pathlib import Path
from datetime import timedelta
from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Sentry initialization
# Only active if SENTRY_DSN is set in .env
_sentry_dsn = config('SENTRY_DSN', default='')
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
        send_default_pii=True,
        environment=config('SENTRY_ENVIRONMENT', default='production'),
    )

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
SECRET_KEY = config('SECRET_KEY', default='django-insecure-0eaq#&d)auhbdsgm%x@%ug7brin89@&+t9*6s1e(5ih%w5o+)6')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=lambda v: [s.strip() for s in v.split(',')])

GOOGLE_CLIENT_ID = '1074628944814-je4b5jgu8uccj26rk9v9i73a8guf0kvn.apps.googleusercontent.com'
GOOGLE_IOS_CLIENT_ID = '1074628944814-mhnit64ojdadqsiegbijkhoctco6nbm8.apps.googleusercontent.com'
GOOGLE_ANDROID_CLIENT_ID = '1074628944814-agasb9aec40t7dttonnetibm8cm2o4nm.apps.googleusercontent.com'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework_simplejwt',  # Add this
    'rest_framework_simplejwt.token_blacklist',
    'rest_framework_extensions',
    'corsheaders',  # Add this for handling CORS
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'mptt',
    'django_elasticsearch_dsl',
    'oauth2_provider',
    'orders',

    'core',
    'products',
    'favorites',
    'django_filters',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # Add this
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'korean_app_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'korean_app_backend.wsgi.application'


# Database
# Set USE_SQLITE=True in .env only for local dev without Docker.
# In production (Docker / any server) always use PostgreSQL.
_use_sqlite = config('USE_SQLITE', default=False, cast=bool)

if _use_sqlite:
    print("[DB] Using SQLite (dev-only mode)")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    print("[DB] Using PostgreSQL")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME', default='korean_app'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default='postgres'),
            'HOST': 'localhost',
            'PORT': config('DB_PORT', default='5432'),
            # Reuse DB connections across requests (reduces ~5ms overhead per request)
            'CONN_MAX_AGE': 60,
        }
    }

AUTH_USER_MODEL = 'core.CustomUser'


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

REST_FRAMEWORK = {
    # Аутентификация
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ] if 'test' not in sys.argv else [],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'login': '5/minute',
        'user': '100/minute',
    },

    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 40,
}


CACHES_REDIS_DISABLED = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URL", default="redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': config('ELASTICSEARCH_URL', default='http://localhost:9200'),
    },
}

# Disable ES auto-indexing signals during tests
if 'test' in sys.argv or 'pytest' in sys.modules:
    ELASTICSEARCH_DSL_SIGNAL_PROCESSOR = 'django_elasticsearch_dsl.signals.BaseSignalProcessor'

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,

    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,

    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',

    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',

    'JTI_CLAIM': 'jti',

    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Settings
# In development (DEBUG=True): allow all origins for easy frontend work.
# In production (DEBUG=False): restrict to specific domains via CORS_ALLOWED_ORIGINS env var.
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    _cors_origins = config('CORS_ALLOWED_ORIGINS', default='')
    CORS_ALLOWED_ORIGINS = [o.strip() for o in _cors_origins.split(',') if o.strip()]

CORS_ALLOW_CREDENTIALS = True


SPECTACULAR_SETTINGS = {
    'TITLE': 'Korean App Backend API',
    'DESCRIPTION': 'Korean language learning application backend',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
# collectstatic writes here; nginx serves from this directory
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media (uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Google OAuth2 Settings
# Get these from Google Cloud Console: https://console.cloud.google.com/apis/credentials
# You need to create OAuth 2.0 Client IDs for:
# 1. Web application (for token verification)
# 2. iOS application  
# 3. Android application
GOOGLE_CLIENT_ID = ''  # Web client ID (required)
GOOGLE_IOS_CLIENT_ID = ''  # iOS client ID (optional, but needed for iOS app)
GOOGLE_ANDROID_CLIENT_ID = ''  # Android client ID (optional, but needed for Android app)

# Local development cache (no Redis needed)
if not config("REDIS_URL", default=""):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
