__all__ = [
    'DataStoreSettingsImproperlyConfiguredException', 'EngineNotImplementedException', 'EngineConnectionException'
]


class DataStoreSettingsImproperlyConfiguredException(Exception):
    def __init__(self, message=None):
        self.value = 'Chatbot NER datastore settings are not configured correctly. Please make sure the required' \
                     ' connection settings are available in the environment variables'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class EngineNotImplementedException(Exception):
    def __init__(self, message=None):
        self.value = "Chatbot NER datastore currently supports only the following engines: ['elasticsearch'] . " \
                     "Please make sure the ENGINE environment variable is correctly set"
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class EngineConnectionException(Exception):
    def __init__(self, message=None, engine='the configured engine'):
        self.value = "Chatbot NER datastore was unable to connect to " + engine + \
                     ". Please make sure the " + engine + " service is reachable."
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)
