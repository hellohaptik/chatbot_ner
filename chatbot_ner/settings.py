"""
Django settings for chatbot_ner project.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from __future__ import absolute_import

import os
import sys

from chatbot_ner.setup_sentry import setup_sentry

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENVIRONMENT = os.environ.get('ENVIRONMENT') or os.environ.get('HAPTIK_ENV')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
TEMPLATE_DEBUG = False
ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'datastore',
    'ner_v1',
    'ner_v2',
    # TODO: drop dependency on `nose`, no longer actively maintained
    'django_nose'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'chatbot_ner.urls'

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

WSGI_APPLICATION = 'chatbot_ner.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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

# setup sentry
setup_sentry()

# APM
_elastic_apm_enabled = (os.environ.get('ELASTIC_APM_ENABLED') or '').strip().lower()
ELASTIC_APM_ENABLED = (_elastic_apm_enabled == 'true') and 'test' not in sys.argv

if ELASTIC_APM_ENABLED:
    ELASTIC_APM_SERVER_URL = os.environ.get('ELASTIC_APM_SERVER_URL')
    ELASTIC_APM = {
        'DEBUG': DEBUG,
        'SERVICE_NAME': 'chatbot_ner',
        'SERVER_URL': ELASTIC_APM_SERVER_URL,
        'SPAN_FRAMES_MIN_DURATION': '5ms',
        'STACK_TRACE_LIMIT': 500,
        'ENVIRONMENT': ENVIRONMENT,
        'TRANSACTION_SAMPLE_RATE': 0.1,
        'TRANSACTION_MAX_SPANS': 500,
        'INSTRUMENT': True,
        'DISABLE_SEND': False,
        'CAPTURE_BODY': 'off',
        'SERVER_TIMEOUT': '2s',
        'API_REQUEST_TIME': '10s',
        'DJANGO_AUTOINSERT_MIDDLEWARE': False,
        'DISABLE_LOG_RECORD_FACTORY': True,
    }
    INSTALLED_APPS.append('elasticapm.contrib.django')
    MIDDLEWARE.append('elasticapm.contrib.django.middleware.TracingMiddleware')

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

if 'test' in sys.argv:
    # FOR TEST CASES - COMMON SETTINGS FOR ALL ENVIRONMENTS
    TEST_DB_PATH = os.environ.get('TEST_DB_PATH') or '/dev/shm/chatbot_ner_test.db.sqlite3'
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_DB_PATH,
        'CONN_MAX_AGE': 60
    }
    MIGRATION_MODULES = {
        'datastore': None,
        'ner_v1': None,
        'ner_v2': None,
    }
    NOSE_ARGS = [
        '--nocapture',
        '--nologcapture',
        '--verbosity=3',
        '--exclude-dir=chatbot_ner/',
        '--exclude-dir=docs/',
        '--exclude-dir=docker/',
        '--exclude-dir=data/',
        '--ignore-files=manage.py',
        '--ignore-files=nltk_setup.py',
        '--ignore-files=__init__.py',
        '--ignore-files=const.py',
        '--ignore-files=constant.py',
        '--ignore-files=constants.py',
        '--ignore-files=run_postman_tests.py',
        '--cover-erase',
        '--cover-package=datastore,external_api,language_utilities,lib,ner_v1,ner_v2',
        '--cover-inclusive',
    ]
