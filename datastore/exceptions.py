__all__ = [
    'DataStoreSettingsImproperlyConfiguredException', 'EngineNotImplementedException', 'EngineConnectionException',
    'IndexForTransferException', 'AliasForTransferException', 'NonESEngineTransferException',
    'IndexNotFoundException', 'InvalidESURLException', 'SourceDestinationSimilarException',
    'InternalBackupException', 'AliasNotFoundException', 'PointIndexToAliasException',
    'FetchIndexForAliasException', 'DeleteIndexFromAliasException', 'DataStoreRequestException'
]


class BaseDataStoreException(Exception):
    DEFAULT_ERROR_MESSAGE = None

    def __init__(self, message=None):
        message = message or self.DEFAULT_ERROR_MESSAGE
        if message:
            super().__init__(message)
        else:
            super().__init__()


class DataStoreSettingsImproperlyConfiguredException(BaseDataStoreException):
    DEFAULT_ERROR_MESSAGE = 'Chatbot NER datastore settings are not configured correctly. ' \
                            'Please make sure the required connection settings are available ' \
                            'in the environment variables'


class EngineNotImplementedException(BaseDataStoreException):
    DEFAULT_ERROR_MESSAGE = 'Chatbot NER datastore currently supports only the following ' \
                            'engines: ["elasticsearch"]. Please make sure the ENGINE environment ' \
                            'variable is correctly set'


class EngineConnectionException(BaseDataStoreException):
    def __init__(self, message=None, engine='configured engine'):
        if not message:
            message = 'Chatbot NER datastore was unable to connect to {engine}. ' \
                      'Please make sure the {engine} service is reachable.'.format(engine=engine)
        super().__init__(message)


class IndexForTransferException(BaseDataStoreException):
    DEFAULT_ERROR_MESSAGE = 'ES index has not been configured for transfer. Please configure before transfer.'


class AliasForTransferException(BaseDataStoreException):
    DEFAULT_ERROR_MESSAGE = 'ES alias has not been configured for transfer. Please configure before transfer.'


class NonESEngineTransferException(BaseDataStoreException):
    DEFAULT_ERROR_MESSAGE = 'Transfer has been triggered for datastore engone other than elastic search'


class IndexNotFoundException(BaseDataStoreException):
    """
    This exception will be raised if index is not found in ES
    """
    pass


class InvalidESURLException(BaseDataStoreException):
    """
    This exception will be raised if the ES URL is invalid
    """
    pass


class SourceDestinationSimilarException(BaseDataStoreException):
    """
    This exception will be raised if source is the same as destination
    """
    pass


class InternalBackupException(BaseDataStoreException):
    """
    This exception will be raised for transfer of documents from one index to other within a ES URL
    """
    pass


class AliasNotFoundException(BaseDataStoreException):
    """
    This exception will be raised if alias not found in ES
    """
    pass


class PointIndexToAliasException(BaseDataStoreException):
    """
    This exception is raised if the assignment of an index to an alias fails
    """
    pass


class FetchIndexForAliasException(BaseDataStoreException):
    """
    This exception is raised if fetch for indices for an alias fails
    """
    pass


class DeleteIndexFromAliasException(BaseDataStoreException):
    """
    This exception is raised if deletion of an index from an alias fails
    """
    pass


class DataStoreRequestException(BaseDataStoreException):
    def __init__(self, message, engine, request, response=None):
        self.engine = engine
        self.request = request
        self.response = response
        super().__init__(message)
