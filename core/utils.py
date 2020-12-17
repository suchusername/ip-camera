import re


def check_ip(ip):
    """
    Check whether a given string is a valid IP address.
    """
    no_port = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ip)
    with_port = re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\:\d{1,4}$", ip)
    return bool(no_port or with_port)


def merge_dicts(*dicts):
    """
    Merge two dictionaries. If keys overlap, later dictionaries overwrite their values.
    
    Args:
    *dicts: sequence of python dicts
    
    Returns:
    dict, merged dictionary
    """
    result = {}
    for dictionary in dicts:
        result.update(dictionary)
    return result


def bool_to_onoff(val):
    if val:
        return "on"
    return "off"
