class BaseException(Exception):
    pass


class APIHandlerException(BaseException):
    """
    This is used to send error messages in response for API call
    on validation errors or handled errors
    """
    def __init__(self, error_msg=''):
        self.error_msg = error_msg

    def __str__(self):
        return self.error_msg
