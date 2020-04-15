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

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
_dj_debug = os.environ.get('DJANGO_DEBUG', 'false')
DEBUG = (_dj_debug and _dj_debug.lower() == 'true')

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

#    MIGRATION_MODULES = DisableMigrations()


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = [
    '--nocapture',
    '--nologcapture',
    '--verbosity=3',
    '--ignore-files=urls.py',
    '--ignore-files=wsgi.py',
    '--ignore-files=manage.py',
    '--ignore-files=nltk_setup.py',
    '--ignore-files=__init__.py',
    '--ignore-files=const.py',
    '--ignore-files=constant.py',
    '--ignore-files=constants.py',
    '--ignore-files=start_server.sh',
    '--ignore-files=settings.py',
    '--exclude-dir=docs/',
    '--exclude-dir=docker/',
    '--exclude-dir=data/',
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
