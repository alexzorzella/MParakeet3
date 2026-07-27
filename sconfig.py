import configparser
from collections import defaultdict

import sys
from pathlib import Path

def resolve_relative_path(filename):
    if getattr(sys, 'frozen', False):
        result = Path(sys.executable).resolve().parent / filename
        return result
    else:
        result = Path(__file__).resolve().parent / filename
        return result

CONFIG_FILENAME = "config.ini"
CONFIG_PATH = resolve_relative_path("config.ini")

def get_config_param(config_section, cast_to, param_name):
    """Returns a config parameter in a passed config section cast to the passed type"""

    try:
        return cast_to(config_section[param_name])
    except:
        return None

def parse_config(config_path=CONFIG_PATH, section="", params: list[tuple[str, type]] | None = None):
    """Parses a config file and returns a dict of parameters, falling back to None if the parameter is not found"""
    return parse_config_with_defaults(config_path=config_path, section=section, params=[(item[0], item[1], None) for item in params])

def parse_config_with_fallbacks(config_path=CONFIG_PATH, section="", params: list[tuple[str, type, object]] | None = None):
    """Parses a config file and returns a dict of parameters, falling back to the passed object in the tuple (config.ini takes precedence over last object)"""
    return parse_config_with_defaults(config_path=config_path, section=section, params=params)

def parse_config_with_overrides(config_path=CONFIG_PATH, section="", params: list[tuple[str, type, object]] | None = None):
    """Parses a config file and returns a dict of parameters, overriding to the passed object in the tuple (last object takes precedence over config.ini)"""
    return parse_config_with_defaults(config_path=config_path, section=section, params=params, override=True)

def parse_config_with_defaults(config_path=CONFIG_PATH, section="", params: list[tuple[str, type, object]] | None = None, override=False):
    default_result = defaultdict(lambda: None, {n: default for n, _, default in params })

    if params is None or len(params) <= 0 or section == "":
        return default_result

    config = configparser.ConfigParser()

    config_path = Path(config_path)

    if not config_path.is_file():
        return default_result
    else:
        config.read(config_path)

        try:
            import_section = config[section]
        except:
            return default_result

        results = defaultdict()

        for parameter in params:
            param_name = parameter[0]
            param_type = parameter[1]
            param_default = parameter[2]

            config_param = get_config_param(config_section=import_section, cast_to=param_type, param_name=param_name)

            if override:
                if param_default is not None:
                    cast_variable = param_default
                else:
                    cast_variable = config_param
            else:
                if config_param is not None:
                    cast_variable = config_param
                else:
                    cast_variable = param_default

            results[param_name] = cast_variable

        return results