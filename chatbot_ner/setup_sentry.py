from __future__ import absolute_import

import os
import sys

# HAPTIK Environment and CAS name
ENVIRONMENT = os.environ.get('ENVIRONMENT') or os.environ.get('HAPTIK_ENV')
CLIENT_APPLICATIONS_SETUP_NAME = os.environ.get('CLIENT_APPLICATIONS_SETUP_NAME')

# Support for Sentry DSN
SENTRY_DSN = os.environ.get('SENTRY_DSN')
_sentry_enabled = (os.environ.get('SENTRY_ENABLED') or '').strip().lower()
SENTRY_ENABLED = (_sentry_enabled == 'true' and 'test' not in sys.argv)


def setup_sentry():
    """
    Setup sentry if enabled in the environment
    """
    if SENTRY_ENABLED:
        import sentry_sdk
        import logging
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.excepthook import ExcepthookIntegration

        def before_sentry_send(event, hint):
            if event.get('logger', None) == 'elasticapm.transport':
                return None
            event.setdefault("tags", {})["cas_name"] = CLIENT_APPLICATIONS_SETUP_NAME
            return event

        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        sentry_exception = ExcepthookIntegration(
            always_run=True
        )
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), sentry_logging, sentry_exception],
            environment=ENVIRONMENT,
            sample_rate=1.0,
            before_send=before_sentry_send
        )
