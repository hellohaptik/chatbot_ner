__all__ = [
    'DataStoreSettingsImproperlyConfiguredException', 'EngineNotImplementedException', 'EngineConnectionException',
    'IndexForTransferException', 'AliasForTransferException', 'NonESEngineTransferException',
    'IndexNotFoundException', 'InvalidESURLException', 'SourceDestinationSimilarException',
    'InternalBackupException', 'AliasNotFoundException', 'PointIndexToAliasException',
    'FetchIndexForAliasException', 'DeleteIndexFromAliasException'

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


class IndexForTransferException(Exception):
    def __init__(self, message=None):
        self.value = "ES index has not been configured for transfer. Please configure before transfer."
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class AliasForTransferException(Exception):
    def __init__(self, message=None):
        self.value = "ES alias has not been configured for transfer. Please configure before transfer."
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class NonESEngineTransferException(Exception):
    def __init__(self, message=None):
        self.value = "Transfer has been triggered for datastore engone other than elastic search"
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class IndexNotFoundException(Exception):
    """
    This exception will be raised if index is not found in ES
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class InvalidESURLException(Exception):
    """
    This exception will be raised if the ES URL is invalid
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class SourceDestinationSimilarException(Exception):
    """
    This exception will be raised if source is the same as destination
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class InternalBackupException(Exception):
    """
    This exception will be raised for transfer of documents from one index to other within a ES URL
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class AliasNotFoundException(Exception):
    """
    This exception will be raised if alias not found in ES
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class PointIndexToAliasException(Exception):
    """
    This exception is raised if the assignment of an index to an alias fails
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class FetchIndexForAliasException(Exception):
    """
    This exception is raised if fetch for indices for an alias fails
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)


class DeleteIndexFromAliasException(Exception):
    """
    This exception is raised if deletion of an index from an alias fails
    """
    def __init__(self, message=None):
        self.value = message

    def __str__(self):
        return repr(self.value)
