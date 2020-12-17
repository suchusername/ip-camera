import requests
import json

IO_CONFIG_PATH = "/ip-camera/config/io_config.json"
with open(IO_CONFIG_PATH, "r") as fd:
    CONNECTION_CONFIG = json.load(fd)["connection"]


class CustomTimeout(requests.adapters.TimeoutSauce):
    def __init__(self, *args, **kwargs):
        if kwargs["connect"] is None:
            kwargs["connect"] = CONNECTION_CONFIG["timeout"]
        if kwargs["read"] is None:
            kwargs["read"] = CONNECTION_CONFIG["timeout"]
        super(CustomTimeout, self).__init__(*args, **kwargs)


requests.adapters.TimeoutSauce = CustomTimeout


def AXIS_request(url, params={}, timeout=None):
    """
    Send a GET request to an AXIS camera and parse it's response.
    
    Args:
    url   : str, where to send a request
    params: dict, parameters
    kwargs: dict, keyword arguments for requests.get()
    
    Returns:
    tuple (ok, data), where
        ok  : bool, if the request was successful
        data: dict or str with whatever the response from the server was
    """
    # Sending GET request
    try:
        resp = requests.get(url, params=params)

    except requests.exceptions.RequestException as e:
        ok = False
        data = "Connection timed out"
        return ok, data

    except:
        ok = False
        data = "Unknown error"
        return ok, data

    # Parsing response
    if resp.status_code >= 400:
        # GET request is unsuccessful

        ok = False
        data = str(resp.status_code) + " " + resp.reason
        return ok, data

    if resp.text.startswith("Error"):
        # GET request is successful, but user submitted invalid parameters

        ok = False
        data = resp.text
        return ok, data

    # We assume that returned data has several lines in format `key=value`

    ok = True
    data = {}

    try:
        for line in resp.text.splitlines():

            (name, var) = line.split("=", 2)
            try:
                data[name.strip()] = float(var)
            except:
                data[name.strip()] = var

    except:

        ok = False
        data = resp.text

    return ok, data
