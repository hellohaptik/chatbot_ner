from __future__ import absolute_import

import os
import sys

# HAPTIK Environment and CAS name
ENVIRONMENT = os.environ.get('ENVIRONMENT') or os.environ.get('HAPTIK_ENV')
CLIENT_APPLICATIONS_SETUP_NAME = os.environ.get('CLIENT_APPLICATIONS_SETUP_NAME') or 'DEFAULT_CAS'

# Support for Sentry DSN
SENTRY_DSN = os.environ.get('SENTRY_DSN')
SENTRY_ENABLED = os.environ.get('SENTRY_ENABLED')
SENTRY_ENABLED = True if SENTRY_ENABLED == 'True' and 'test' not in sys.argv else False


def setup_sentry():
    """
    Setup sentry if enabled in the environment
    """
    if SENTRY_ENABLED:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        def before_sentry_send(event, hint):
            event.setdefault("tags", {})["cas_name"] = CLIENT_APPLICATIONS_SETUP_NAME
            return event

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration(), LoggingIntegration()],
            environment=ENVIRONMENT,
            sample_rate=0.1,
            before_send=before_sentry_send
        )
