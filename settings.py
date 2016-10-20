import logging
from typing import Dict

import yaml
import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


def _merge(source: Dict, destination: Dict) -> Dict:
    for key, value in source.items():
        if isinstance(value, dict):
            node = destination.setdefault(key, {})
            _merge(value, node)
        else:
            destination[key] = value
    return destination


def _env_var_eval(val: Dict):
    logger = logging.getLogger(__name__)
    for key, value in val.items():
        if isinstance(value, dict):
            _env_var_eval(value)
        elif isinstance(value, str) and value[:1] == '$':
            val[key] = os.environ.get(value[1:], None)
            if not val[key]:
                logger.warning('Environment variable %s is not defined' % value[1:])
    return val


class _ParamBridge:
    INTEGRATOR_PARAM_FILENAME = 'param.in'
    INTEGRATOR_BIG_FILENAME = 'big.in'

    def __init__(self, config_path: str, local_config_path: str = None):
        with open(config_path) as f:
            try:
                self._params = yaml.load(f)
            except Exception as e:
                raise e

        if local_config_path and os.path.exists(local_config_path):
            local_params = {}
            with open(local_config_path) as f:
                try:
                    local_params = yaml.load(f)
                except Exception as e:
                    raise e

            if local_params:
                self._params = _merge(local_params, self._params)
        self._params = _env_var_eval(self._params)

    def __getitem__(self, key: str):
        return getattr(self, key, self._params[key])


class Config:
    _project_dir = _PROJECT_DIR
    _params = None

    @classmethod
    def get_params(cls) -> _ParamBridge:
        """
        :rtype: dict
        """
        local_config_filename = None
        if 'pytest' in ' '.join(sys.argv):
            config_filename = 'config_unittest.yml'
        else:
            config_filename = 'config.yml'
            local_config_filename = 'local_config.yml'
        if not cls._params:
            config_dir = os.path.join(cls._project_dir, 'config')
            if local_config_filename:
                local_config_path = os.path.join(config_dir, local_config_filename)
            else:
                local_config_path = None
            cls._params = _ParamBridge(os.path.join(config_dir, config_filename),
                                       local_config_path)

        return cls._params

    @classmethod
    def get_project_dir(cls):
        return cls._project_dir
