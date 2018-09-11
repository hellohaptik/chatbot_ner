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


class ESTrainingTextListError(Exception):
    """
    This exception is raised if training data index is not setup
    """

    def __init__(self, message=None):
        self.value = 'There is no text present in the elastic search for training the model'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class ESTrainingEntityListError(Exception):
    """
    This exception is raised if training data index is not setup
    """

    def __init__(self, message=None):
        self.value = 'There is no Entity List present in the elastic search for training the model'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)