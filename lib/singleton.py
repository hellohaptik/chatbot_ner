
class Singleton(type):
    """
    A pythonic Singleton implementation to be implemented with metaclass. Based on the pros and cons from
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python


    This is a Singleton metaclass. All classes affected by this metaclass
    have the property that only one instance is created for each set of arguments
    passed to the class constructor.


    Sample Implementation:

    #Python2
    class MyClass(BaseClass):
        __metaclass__ = Singleton

    #Python3
    class MyClass(BaseClass, metaclass=Singleton):
        pass

    """

    def __init__(cls, name, bases, dict):
        super(Singleton, cls).__init__(cls, bases, dict)
        cls._instanceDict = {}

    def __call__(cls, *args, **kwargs):
        argdict = {'args': args}
        argdict.update(kwargs)
        argset = frozenset(sorted(argdict.items()))
        if argset not in cls._instanceDict:
            cls._instanceDict[argset] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instanceDict[argset]

