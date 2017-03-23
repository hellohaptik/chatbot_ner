__all__ = [
    'DataStoreSettingsImproperlyConfiguredException', 'EngineNotImplementedException',
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
