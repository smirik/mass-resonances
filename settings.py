import yaml
import os
import sys

_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


class _ParamBridge:
    INTEGRATOR_PARAM_FILENAME = 'param.in'
    INTEGRATOR_BIG_FILENAME = 'big.in'

    def __init__(self, path: str):
        with open(path) as f:
            try:
                self._params = yaml.load(f)
            except Exception as e:
                raise e

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
        if 'pytest' in ' '.join(sys.argv):
            config_filename = 'config_unittest.yml'
        else:
            config_filename = 'config.yml'
        if not cls._params:
            path = os.path.join(cls._project_dir, 'config', config_filename)
            cls._params = _ParamBridge(path)
        return cls._params

    @classmethod
    def get_project_dir(cls):
        return cls._project_dir
