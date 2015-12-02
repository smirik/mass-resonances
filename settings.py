import yaml
import os


_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


class _ParamBridge:
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
    def get_params(cls) -> dict:
        """

        :rtype: dict
        """
        if not cls._params:
            path = os.path.join(cls._project_dir, 'config', 'config.yml')
            cls._params = _ParamBridge(path)
        return cls._params

    @classmethod
    def get_project_dir(cls):
        return cls._project_dir

    @classmethod
    def set_project_dir(cls, value: str):
        cls._project_dir = value
