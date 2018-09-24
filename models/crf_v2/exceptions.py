class AwsCrfModelWriteException(Exception):
    """
    This exception is raised if writing to the Aws model has failed
    """

    def __init__(self, message=None):
        self.value = 'Aws write for the crf model has failed'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class ESCrfTrainingTextListNotFoundException(Exception):
    """
    This exception is raised if text for training Crf Model is not found
    """

    def __init__(self, message=None):
        self.value = 'There is no text present in the elastic search for training crf the model'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)


class ESCrfTrainingEntityListNotFoundException(Exception):
    """
    This exception is raised if Entity List for training Crf Model is not found
    """

    def __init__(self, message=None):
        self.value = 'There is no Entity List present in the elastic search for training the model'
        if message:
            self.value = message

    def __str__(self):
        return repr(self.value)