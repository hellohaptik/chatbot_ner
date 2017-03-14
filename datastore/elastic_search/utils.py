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
