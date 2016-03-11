import os

from settings import Config


class ResonanceDatabase(object):
    CONFIG = Config.get_params()
    PROJECT_DIR = Config.get_project_dir()
    DBPATH = os.path.join(PROJECT_DIR, CONFIG['resonance']['db_file'])

    def __init__(self, db_file: str = DBPATH):
        """

        :type db_file: str
        """

        self.db_file = db_file
        self._create_if_not_exists()

    def add_string(self, value: str):
        tmp = value.split(';')
        s = '%s;%s' % (tmp[0], tmp[1])
        if not self._check_string(s):
            with open(self.db_file, 'a+') as db:
                db.write('%s\n' % value)

    def _check_string(self, value: str) -> bool:
        with open(self.db_file, 'r') as f:
            for line in f:
                if value in line:
                    return True
        return False

    def _create_if_not_exists(self):
        if not os.path.exists(self.db_file):
            self._create()

    def _create(self):
        dir_path = os.path.dirname(self.db_file)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        f = open(self.db_file, 'w')
        f.close()
