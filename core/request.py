import requests


def AXIS_request(url, params={}):
    """
    Send a GET request to an AXIS camera and parse it's response.
    
    Args:
    url   : str, where to send a request
    params: dict, parameters
    
    Returns:
    tuple (ok, data), where
        ok  : bool, if the request was successful
        data: dict or str with whatever the response from the server was
    """
    # Sending GET request
    resp = requests.get(url, params=params)

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
