import yaml
import os


_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


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
            with open(path) as f:
                try:
                    cls._params = yaml.load(f)
                except Exception as e:
                    raise e
        return cls._params

    @classmethod
    def get_project_dir(cls):
        return cls._project_dir

    @classmethod
    def set_project_dir(cls, value: str):
        cls._project_dir = value
