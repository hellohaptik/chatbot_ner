from django.core.cache import caches
cached_ml = caches['redis_ml']
cached_ml_dest = caches['redis_ml_dest']


def set_cache_ml(variable_name, variable_value, expiry_time=172800):
    """
    Stores the cache data in  a cache
    Args:
        variable_name (str): Key for the redis cache
        variable_value (str): Value for the given key
        expiry_time (str): Expiry time settings

    Returns:
        status (bool): Status indication if the set_cache was successful
    """
    return cached_ml.set(variable_name, variable_value, expiry_time)


def get_cache_ml(variable_name):
    """
    Gets data from cache
    Args:
        variable_name (str): Key for the redis cache

    Returns:
        status (bool): Status indication if the set_cache was successful
    """
    return cached_ml.get(variable_name)


def set_cache_ml_dest(variable_name, variable_value, expiry_time=172800):
    """
    Stores the cache data in destination cache
    Args:
        variable_name (str): Key for the redis cache
        variable_value (str): Value for the given key
        expiry_time (str): Expiry time settings

    Returns:
        status (bool): Status indication if the set_cache was successful
    """
    return cached_ml_dest.set(variable_name, variable_value, expiry_time)
