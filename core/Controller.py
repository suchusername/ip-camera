import os
import requests
import time
import json
import re

DEFAULT_CAMERA_CONFIG = "/ip-camera/config/default_camera_config.json"
IO_CONFIG = "/ip-camera/config/io_config.json"

PRESETS_PATH = "/ip-camera/config/camera_presets"


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
    
    Arguments:
    ip       : str, ip address of an AXIS camera
    camera_n : int, number of a camera in the network
    camera_ir: int, rotation of a camera (0 or 180, defaults to 0)
    
    Properties:
    ip         : str, ip address of an AXIS camera
    camera_n   : int, number of a camera in the network
    camera_ir  : int, rotation of a camera (0 or 180, defaults to 0)
    base_config: dict, base configurations of the camera
    url        : str, where to send GET requests
    limits     : dict, limits of the camera
    presents   : list, available presets
    
    Note: every `set` or `get` method returns response data.
    """

    def __init__(self, ip, camera_n=1, camera_ir=0):

        self.ip = ip
        self.camera_n = camera_n
        self.camera_ir = camera_ir
        self._limits = None
        with open(IO_CONFIG, "r") as fd:
            self._io_config = json.load(fd)

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

    @property
    def presets(self):
        l = [x for x in os.listdir(PRESETS_PATH) if x.endswith(".json")]
        l = [x[: -len(".json")] for x in l]
        return l

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

    def save_preset(self, name, overwrite=False):
        """
        Save current configuration as a preset.
        
        Args:
        name     : str, name of a preset
        overwrite: bool, whether to overwrite a current preset if it already exists
        """
        # Checking name
        if not re.match(self._io_config["preset"]["regexp"], name):
            return "preset name must contain only letters, numbers or underscores"
        preset_len = self._io_config["preset"]["len"]
        if len(name) > preset_len:
            return f"preset name must not exceed {preset_len} characters"

        # Counting existing presents
        preset_max = self._io_config["preset"]["max"]
        if len(self.presets) >= preset_max:
            return f"maximum number of presets ({preset_max}) reached"

        save_path = os.path.join(PRESETS_PATH, name + ".json")
        if os.path.exists(save_path) and (not overwrite):
            return "preset already exists"

        config = self.get_configuration()
        with open(save_path, "w") as fd:
            json.dump(config, fd, indent=4)

    def load_preset(self, name):
        """
        Load a preset.
        
        Args:
        name: str, name of a preset
        """
        if not re.match(self._io_config["preset"]["regexp"], name):
            return "preset doesn't exist"
        if len(name) > self._io_config["preset"]["len"]:
            return "preset doesn't exist"

        preset_path = os.path.join(PRESETS_PATH, name + ".json")
        if not os.path.exists(preset_path):
            return "preset doesn't exist"

        with open(preset_path, "r") as fd:
            config = json.load(fd)

        resp_data = self.configure(config)
        return resp_data

    def delete_preset(self, name):
        """
        Delete an existing preset.
        
        Args:
        name: str, name of a preset
        """
        if not re.match(self._io_config["preset"]["regexp"], name):
            return "preset doesn't exist"
        if len(name) > self._io_config["preset"]["len"]:
            return "preset doesn't exist"

        preset_path = os.path.join(PRESETS_PATH, name + ".json")
        if not os.path.exists(preset_path):
            return "preset doesn't exist"

        os.remove(preset_path)

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
        Toggle autoiris (an iris is the part of the camera that controls how much light comes through the lens).
        
        Args:
        val: True/False or "on"/"off"
        """
        if isinstance(val, bool):
            config = {"autoiris": bool_to_onoff(val)}
        else:
            config = {"autoiris": val}
        resp_data = self.configure(config)
        return resp_data

    def tilt(self, val=None, up=True):
        """
        Tilt camera up or down. Positive values for "up" correspond to tilting upwards.
        
        Args:
        val: float, angle to rotate (if None, default value is taken)
        up : bool, True - move up, False - move down
        """
        if val is None:
            val = self._io_config["user"]["tilt_offset"]
        if not up:
            val = -val

        config = {"rtilt": val}
        resp_data = self.configure(config)
        return resp_data

    def pan(self, val=None, right=True):
        """
        Pan camera left or right. Positive values for "right" correspond to rotating to the right.
        
        Args:
        val  : float, angle to rotate (if None, default value is taken)
        right: bool, True - move right, False - left
        """
        if val is None:
            val = self._io_config["user"]["pan_offset"]
        if not right:
            val = -val

        config = {"rpan": val}
        resp_data = self.configure(config)
        return resp_data

    def zoom(self, val=None, closer=True):
        """
        Zoom in or zoom out. Positive values for "closer" correspond to zooming in.
        
        Args:
        val   : float, relative zoom (if None, default value is taken)
        closer: bool, True - zoom in, False - zoom out
        """
        if val is None:
            val = self._io_config["user"]["zoom_offset"]
        if not closer:
            val = -val

        config = {"rzoom": val}
        resp_data = self.configure(config)
        return resp_data
