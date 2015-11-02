import yaml
import os

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


class ConfigSingleton:
    _inst = None

    @classmethod
    def get_singleton(cls) -> dict:
        """

        :rtype: dict
        """
        if not cls._inst:
            path = os.path.join(PROJECT_DIR, 'config', 'config.yml')
            with open(path) as f:
                try:
                    cls._inst = yaml.load(f)
                except Exception as e:
                    raise e
        return cls._inst
