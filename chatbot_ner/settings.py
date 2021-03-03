"""
Django settings for predictive_server project.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from __future__ import absolute_import

import os
import sys

from chatbot_ner.setup_sentry import setup_sentry

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ENVIRONMENT = os.environ.get('ENVIRONMENT') or os.environ.get('HAPTIK_ENV')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

TEMPLATE_DEBUG = False

ALLOWED_HOSTS = ['*']

# setup sentry

setup_sentry()

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
    'models',
    'django_nose'
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# APM
_elastic_apm_enabled = (os.environ.get('ELASTIC_APM_ENABLED') or '').strip().lower()
ELASTIC_APM_ENABLED = (_elastic_apm_enabled == 'true') and 'test' not in sys.argv
ELASTIC_APM_SERVER_URL = os.environ.get('ELASTIC_APM_SERVER_URL')
if ELASTIC_APM_ENABLED:
    ELASTIC_APM = {
        'DEBUG': DEBUG,
        'SERVICE_NAME': 'chatbot_ner',
        'SERVER_URL': ELASTIC_APM_SERVER_URL,
        'SPAN_FRAMES_MIN_DURATION': '5ms',
        'STACK_TRACE_LIMIT': 500,
        'ENVIRONMENT': ENVIRONMENT,
        'TRANSACTION_SAMPLE_RATE': '0.1',
        'TRANSACTION_MAX_SPANS': 500,
        'INSTRUMENT': 'True',
        'DISABLE_SEND': 'False',
        'CAPTURE_BODY': 'off',
        'SERVER_TIMEOUT': '2s',
    }
    INSTALLED_APPS.append('elasticapm.contrib.django')
    MIDDLEWARE.append('elasticapm.contrib.django.middleware.TracingMiddleware')

ROOT_URLCONF = 'chatbot_ner.urls'

WSGI_APPLICATION = 'chatbot_ner.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# FOR TEST CASES - COMMON SETTINGS FOR ALL ENVIRONMENTS


class DisableMigrations(object):

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Keeping this block here for ease in the future
TEST_DB_PATH = os.environ.get('TEST_DB_PATH') or '/dev/shm/chatbot_ner_test.db.sqlite3'

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': TEST_DB_PATH,
        'CONN_MAX_AGE': 60
    }

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
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
    '--cover-package=datastore,external_api,language_utilities,lib,models,ner_v1,ner_v2',
    '--cover-inclusive',
]

# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'
