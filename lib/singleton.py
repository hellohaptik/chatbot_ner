
class Singleton(type):
    """
    A pythonic Singleton implementation to be implemented with metaclass. Based on the pros and cons from
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python

    Sample Implementation:

    #Python2
    class MyClass(BaseClass):
        __metaclass__ = Singleton

    #Python3
    class MyClass(BaseClass, metaclass=Singleton):
        pass

    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
