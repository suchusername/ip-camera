import requests
import time
import json

DEFAULT_CAMERA_CONFIG = "/ip-camera/config/default_camera_config.json"

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

class AXISCameraController:
    """
    Controller of AXIS IP-camera.
    """

    def __init__(self, ip, camera_n=1, camera_ir=0):

        self.ip = ip
        self.camera_n = camera_n
        self.camera_ir = camera_ir
        self._limits = None

    @property
    def base_config(self):
        ret = {}
        ret["camera"] = self.camera_n
        ret["imagerotation"] = self.camera_ir
        ret["html"] = "no"
        ret["timestamp"] = int(time.time())
        return ret

    @property
    def url(self):
        return "http://" + self.ip + "/axis-cgi/com/ptz.cgi"
    
    @property
    def limits(self):
        if self._limits is None:
            config = {"query": "limits"}
            self._limits = self.configure(config)
        return self._limits

    def configure(self, config):
        """
        Set a particular configuration of the camera. 
        Can also be used to get internal state of the camera.
        
        Args:
        config: dict, keys are parameters that need to be set
        
        Returns:
        dict, camera's response
        """
        # Sending GET request
        params = merge_dicts(config, self.base_config)
        resp = requests.get(self.url, params=params)

        # Parsing response
        resp_data = {}
        if resp.text.startswith("Error"):
            print(resp.text)
        else:
            for line in resp.text.splitlines():
                (name, var) = line.split("=", 2)
                try:
                    resp_data[name.strip()] = float(var)
                except ValueError:
                    resp_data[name.strip()] = var
                    
        return resp_data
                    
    def get_configuration(self):
        """
        Get current configuration of a camera.
        
        Args: None
        
        Returns:
        dict with confugurations
        """
        query_config = {"query": "position"}
        resp_data = self.configure(query_config)
        return resp_data
    
    def set_default(self, config=DEFAULT_CAMERA_CONFIG):
        """
        Set default settings.
        
        Args:
        config, dict or path json-file with default settings
        """
        if isinstance(config, str):
            with open(config, "r") as fd:
                config = json.load(fd)
        
        resp_data = self.configure(config)
        return resp_data
    
    def set(self, key, value):
        """
        Set a specific parameter.
        
        Args:
        key  : name of a parameter
        value: value
        """
        config = {key: value}
        resp_data = self.configure(config)
        return resp_data
    
    def autofocus(self, val):
        """
        Toggle autofocus on a camera.
        
        Args:
        val: True/False or "on"/"off"
        """
        if isinstance(val, bool):
            config = {"autofocus": bool_to_onoff(val)}
        else:
            config = {"autofocus": val}
        resp_data = self.configure(config)
        return resp_data
        
    def autoiris(self, val):
        """
        Toggle autoiris (a camera iris is the part of the camera that controls how much light comes through the lens).
        
        Args:
        val: True/False or "on"/"off"
        """
        if isinstance(val, bool):
            config = {"autoiris": bool_to_onoff(val)}
        else:
            config = {"autoiris": val}
        resp_data = self.configure(config)
        return resp_data
        
    
