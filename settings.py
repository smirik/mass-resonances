from typing import Dict

import yaml
import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


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

            self._params = self._merge(local_params, self._params)

    def _merge(self, source: Dict, destination: Dict) -> Dict:
        for key, value in source.items():
            if isinstance(value, dict):
                node = destination.setdefault(key, {})
                self._merge(value, node)
            else:
                destination[key] = value
        return destination

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
