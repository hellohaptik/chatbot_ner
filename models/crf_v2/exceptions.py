class AwsWriteEntityFail(Exception):
    """
    This exception is raised if training data index is not setup
    """

    def __init__(self, message=None):
        self.value = 'Aws write for has entity has failed'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class RedisWriteEntityFail(Exception):
    """
    This exception is raised if training data index is not setup
    """

    def __init__(self, message=None):
        self.value = 'Redis write for has entity has failed'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)