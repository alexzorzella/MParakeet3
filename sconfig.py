import configparser
from collections import defaultdict
from pathlib import Path

from ottlog import logger

def get_config_param(config_filename, config_section, cast_to, param_name):
    try:
        return cast_to(config_section[param_name])
    except:
        error = f"{param_name} not found in {config_filename}."
        logger.exception(error)

        return None

def parse_config(config_filename="config.ini", section="", params: list[tuple[str, type]] | None = None):
    if params is None or len(params) <= 0 or section == "":
        return []

    config = configparser.ConfigParser()

    config_path = Path(config_filename)

    if not config_path.is_file():
        error = f"{config_filename} not found. Please create a config file."

        logger.error(error)
        raise (FileNotFoundError(error))
    else:
        config.read(config_filename)

        try:
            import_section = config[section]
        except:
            return []

        results = defaultdict()

        for parameter in params:
            name = parameter[0]
            type = parameter[1]

            cast_variable = get_config_param(config_filename=config_filename, config_section=import_section, cast_to=type, param_name=name)
            results[name] = cast_variable

        return results