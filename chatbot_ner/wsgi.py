"""
WSGI config for predictive_server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""
from __future__ import absolute_import
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatbot_ner.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
