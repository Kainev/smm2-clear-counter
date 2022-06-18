import toml
import copy

from as64.paths import base_path

_config = {}
_defaults = {}
_rollback = {}

_CONFIG_FILE = base_path("config")
_DEFAULTS_FILE = base_path("defaults")


def get(section, key=None):
    global _config

    if not _config:
        load()

    try:
        if key:
            return _config[section][key]
        else:
            return _config[section]
    except KeyError:
        if key:
            return get_default(section, key)
        else:
            return get_default(section)


def get_default(section, key=None):
    global _defaults

    if not _defaults:
        load_defaults()

    try:
        if key:
            return _defaults[section][key]
        else:
            return _defaults[section]
    except KeyError:
        return None


def set(section, key, value):
    global _config

    _config[section][key] = value


def create_rollback():
    global _rollback
    global _config

    _rollback = copy.deepcopy(_config)


def rollback():
    global _rollback

    if _rollback:
        global _config
        _config = copy.deepcopy(_rollback)
        _rollback = None


def load():
    global _config

    try:
        with open(_CONFIG_FILE) as file:
            _config = toml.load(file)
    except FileNotFoundError:
        generate()


def save():
    global _config
    global _rollback

    try:
        with open(_CONFIG_FILE, 'w') as file:
            toml.dump(_config, file)

        _rollback = None
    except FileNotFoundError:
        pass
    except PermissionError:
        pass


def load_defaults():
    global _defaults

    with open(_DEFAULTS_FILE) as file:
        _defaults = toml.load(file)


def generate():
    global _config

    load_defaults()
    _config = copy.deepcopy(_defaults)
    save()
