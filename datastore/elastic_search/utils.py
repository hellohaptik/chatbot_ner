import inspect
from chatbot_ner.config import USE_ES8_CLIENT

def filter_kwargs(kwargs, keep_kwargs_keys):
    """
    Removes keys and their values from kwargs dictionary if they are absent in keep_kwargs_keys" \

    Args:
        kwargs: dictionary to remove key,values from
        keep_kwargs_keys: A list of keys to keep in the returned dictionary

    Returns:
            A new dictionary with only those keys mentioned in keep_kwargs_keys.
    """
    keep_kwargs = {}
    for key in keep_kwargs_keys:
        if key in kwargs:
            keep_kwargs[key] = kwargs[key]

    return keep_kwargs


def filter_kwargs_from_function(kwargs, fn):
    """
    For a given function object remove all the kwargs which are not present in arguments of that function.

    Args:
        kwargs: dictionary to remove key,value from
        fn: function object for kwarge reference

    Returns:
        A new dictionary with only those keys which are there in function argument

    Example:
        def get_something(name, age=10, hobbies=None): return "Good"

        filter_kwargs_from_function({'name': 'John', 'age': 34, 'id': 1234, 'tag': 'admin'}, get_something)
        # Result : {'name': 'John', 'age': 34}
    """
    signature = inspect.signature(fn)
    filter_keys = [p.name for p in signature.parameters.values()]
    return {key: kwargs[key] for key in filter_keys if key in kwargs}

def filter_es_kwargs(kwargs, fn):
    """
    ES8 have strictness over kwargs and raise exception in case invalid kwarg is passed
    Therefore, need to filter kwargs for given ES fn in case we are using ES8
    """
    if USE_ES8_CLIENT:
        kwargs = filter_kwargs_from_function(kwargs, fn)
    return kwargs