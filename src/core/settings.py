"""
Django settings for core project.
Django 5.1.2
"""

from pathlib import Path
from datetime import timedelta , datetime
from dotenv import load_dotenv
import os

#^ Load environment variables from .env file
load_dotenv()

#^ Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

#^ SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

#^ SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost','127.0.0.1']




#^ Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #* Libs
    'corsheaders',
    'rest_framework',
    'rest_framework_api_key',
    'rest_framework_simplejwt',
    'storages',
    'django_filters',
    #* Apps
    'student',
    'teacher',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


#^ DATABASES

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""

#^ Password validation
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


#^ Internationalization
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


#^ < ==========================Static Files========================== >
STATIC_URL = 'static/'
#STATICFILES_DIRS = os.path.join(BASE_DIR, 'static')
STATIC_ROOT = 'static/'

#^ < ==========================Media Files========================== >
MEDIA_URL = 'media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_NUMBER_FIELDS=50000


#^ < ==========================CACHES CONFIG========================== >

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',  
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


#^ < ==========================REST FRAMEWORK SETTINGS========================== >

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend'
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',    # For anonymous users
        'rest_framework.throttling.UserRateThrottle',    # For authenticated users
    ],

    'DEFAULT_THROTTLE_RATES': {
        'anon': '200/day',   # Limit anonymous users to 10 requests per day
        'user': '3000/hour' # Limit authenticated users to 1000 requests per hour
    },

    'DEFAULT_PAGINATION_CLASS': 'core.pagination.CustomPageNumberPagination',
    'PAGE_SIZE': 100,
}




# ^ < ==========================AUTHENTICATION CONFIG========================== >

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=3),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=3),
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": "Bearer",
    "AUTH_HEADER_NAME": "HTTP_AUTH",
}

# ^ < ==========================CORS ORIGIN CONFIG========================== >

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'Auth',
    'Authorization',
    'Content-Type',  
]

CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'PATCH',
    'DELETE',
]

#^ <==========================APPS CREDENTIALS==========================>

#* VDO CREDENTIALS
VDO_API_KEY = os.getenv('VDO_API_KEY')


#* WHATSAPP CREDENTIALS
WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
WHATSAPP_ID = os.getenv('WHATSAPP_ID')


#* FAWRY CREDENTIALS PRODUCTION
"""
MERCHANT_CODE = os.getenv('MERCHANT_CODE')
MERCHANT_SEC_KEY = os.getenv('MERCHANT_SEC_KEY')
FAWRY_URL= os.getenv('FAWRY_URL')
"""

#* FAWRY CREDENTIALS TEST
MERCHANT_CODE = os.getenv('MERCHANT_CODE_TEST')
MERCHANT_SEC_KEY = os.getenv('MERCHANT_SEC_KEY_TEST')
FAWRY_URL = os.getenv('FAWRY_URL_TEST')
FAWRY_PAYMENT_EXPIRY = int((datetime.now() + timedelta(days=2)).timestamp() * 1000)


# ^ < ==========================CELERY CONFIG========================== >

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_RESULT_EXTENDED = True
CELERY_TASK_TRACK_STARTED = True


# ^ < ==========================AWS CONFIG========================== >

"""
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME')
AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_HEADERS = None
AWS_S3_VERIFY = True
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

"""


# ^ < ==========================PROJECT CONFIG========================== >
WATCHED_PERCENTAGE = os.getenv('WATCHED_PERCENTAGE')
BASE_URL = os.getenv('BASE_URL') 
FRONT_BASE_URL = os.getenv('FRONT_BASE_URL') 
PLATFORM_NAME = os.getenv('PLATFORM_NAME') 
USE_WHATSAPP = False
API_KEY_MANASA = '5d84f5b2-304f-493f-ada5-c0bd3d468135'
API_KEY_MOBILE = '#'
REQUEST_DELAY = 2
BUILD_NUMBER = "11"
APP_VERSION = "1.2.2"