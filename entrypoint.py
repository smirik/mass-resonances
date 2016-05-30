#!/usr/bin/env python
from typing import List
import traceback
import os
import subprocess
import sys
import shutil
import glob
import yaml
import re
from os.path import join as opjoin
import tarfile

TAIL_MESSAGE = 'option not pointed.'
AWS_S3_AEI_FILE_LIST = 'aws_s3_aei_files.txt'
S3_BUCKET_NAME = 'astronomy-out'
S3_AEI_FOLDER = 'aei'


def _copy_aws_file_list(to_project_path):
    shutil.copy(
        opjoin('/opt', 'catalog', AWS_S3_AEI_FILE_LIST),
        opjoin(to_project_path, 'catalog'))


def _copy_catalog(to_project_path):
    shutil.copy(
        opjoin('/opt', 'catalog', 'allnum.cat'),
        opjoin(to_project_path, 'catalog'))


def _copy_aei(from_project_path):
    for item in glob.iglob(opjoin(from_project_path, 'mercury', '*.aei')):
        shutil.copy(item, opjoin('/opt', 'aei'))


def _load_aei(to_project_path: str, start: int, stop: int):
    def _copy_file(by_name):
        path = opjoin('/opt', 'aei', by_name)
        try:
            shutil.copy(path, opjoin(to_project_path, 'mercury'))
        except FileNotFoundError:
            print("%s doesn't exist" % path)

    for i in range(start, stop):
        _copy_file('A%i.aei' % i)

    for name in ['EARTHMOO.aei', 'JUPITER.aei', 'MARS.aei', 'MERCURY.aei', 'NEPTUNE.aei',
                 'PLUTO.aei', 'SATURN.aei', 'URANUS.aei', 'VENUS.aei']:
        _copy_file(name)


def _edit_config(in_project_path: str, url: str):
    orig = opjoin(in_project_path, 'alembic.ini')
    os.rename('%s.dist' % orig, orig)
    copy = opjoin(in_project_path, 'alembic.ini.bck')
    shutil.move(orig, copy)
    with open(copy, 'r') as copy_f:
        with open(orig, 'w') as orig_f:
            for line in copy_f:
                if line.startswith('# sqlalchemy.url'):
                    line = 'sqlalchemy.url=%s' % url
                orig_f.write('%s' % line)
    os.remove(copy)


def _get_signs():
    env_vars = ['RESONANCES_DB_USER',
                'POSTGRES_ENV_POSTGRES_PASSWORD',
                'POSTGRES_PORT_5432_TCP_ADDR',
                'RESONANCES_DB_NAME']
    flag = env_vars[0]
    for var in env_vars[1:]:
        flag = flag and var
    if not flag:
        print('environment variables %s, %s, %s, %s are not set maybe ' % tuple(env_vars) +
              'you\'ve forgot links to postgres docker or point RESONANCES_DB_NAME')
        sys.exit(-1)

    username = os.environ.get(env_vars[0])
    password = os.environ.get(env_vars[1])
    host = os.environ.get(env_vars[2])
    dbname = os.environ.get(env_vars[3])
    return username, password, host, dbname


def _add_redis_sings(to_config_path):
    with open(to_config_path, 'w') as f:
        local_settings = {
            'redis': {
                'host': os.environ.get('REDIS_PORT_6379_TCP_ADDR', 'localhost'),
                'port': os.environ.get('REDIS_PORT_6379_TCP_PORT', 6379),
                'db': 0
            }
        }
        if 'ASTEROID_EPOCH_START' in os.environ:
            local_settings.update({'integrator': {
                'start': os.environ['ASTEROID_EPOCH_START']
            }})
        resonance_section = {}
        if 'AXIS_SWING' in os.environ:
            resonance_section.update({'axis_error': float(os.environ['AXIS_SWING'])})
        if 'PLANETS' in os.environ:
            first_planet, second_planet = os.environ['PLANETS'].split(',')
            resonance_section.update({'bodies': [
                first_planet.strip().upper(), second_planet.strip().upper()
            ]})
        if resonance_section:
            local_settings.update({'resonance': resonance_section})

        f.write(yaml.dump(local_settings))


def _remove(path):
    for item in glob.iglob(path):
        try:
            os.remove(item)
        except Exception as e:
            print(e.args)


def _archive_plots(archive_path: str, source: str, spec: str):
    with tarfile.open(archive_path, spec) as tarf:
        for item in glob.iglob(source):
            tarf.add(item, arcname=os.path.basename(item))


def _get_interval(start: int, stop: int):
    return ['--start=%i' % start, '--stop=%i' % stop]


class ProgramRunner:
    STEP = 100
    CMD = 's3cmd'
    CMD_GET_ARGS = [
        '--access_key=%s' % os.environ.get('S3_ACCESS_KEY', ''),
        '--secret_key=%s' % os.environ.get('S3_SECRET_KEY', ''),
        'get'
    ]
    CMD_SYNC_ARGS = [
        '--acl-private',
        '--bucket-location=EU',
        '--guess-mime-type',
        '--storage-class=STANDARD',
        '--access_key=%s' % os.environ.get('S3_ACCESS_KEY', ''),
        '--secret_key=%s' % os.environ.get('S3_SECRET_KEY', ''),
        'sync',
    ]
    LOGFILE = 'entrypoint-errors.log'
    CALC_LOGFILE = 'resonances-calc.log'
    FIND_LOGFILE = 'resonances-find.log'
    PLOT_LOGFILE = 'resonances-plot.log'
    EXTRACT_ARCHIVE_PATH = '_resonances_archive_root'
    S3_PLOTS_DIR = os.environ.get('S3_PLOTS_DIR', None)

    def __init__(self, project_path, start: int, stop: int):
        if start is None:
            print("warning: --start option not pointed")
        if stop is None:
            print("warning: --stop option not pointed")
        self._stop = stop
        self._start = start
        self._project_path = project_path
        self.S3_ROOT_DIR = os.environ.get('S3_ROOT_DIR')

    def run_find_plot(self, phase_storage: str = 'REDIS', only_librations: bool = False):
        if not self.S3_PLOTS_DIR:
            print('You must to point directory name for plots on AWS S3 (env var S3_PLOTS_DIR)')
            exit(-1)
        assert self.S3_ROOT_DIR
        _copy_aws_file_list(self._project_path)
        _add_redis_sings(opjoin(self._project_path, 'config', 'local_config.yml'))
        file_list_path = opjoin(self._project_path, 'catalog', AWS_S3_AEI_FILE_LIST)
        if not os.path.exists(file_list_path):
            self._raw_log('%s doesn\'t exists. Get list of aei files, that you need.' %
                          file_list_path + ' Try command get_file_list', False)
            return

        with open(file_list_path) as file_list_file:
            for i in range(self._start):
                next(file_list_file)

            for i, line in enumerate(file_list_file):
                if i >= (self._stop - self._start):
                    break
                s3_path = line.split()[3]

                starts_from = line.index('aei-') + 4
                ends_by = line.index('-', starts_from)
                start_asteroid_number = int(line[starts_from: ends_by])

                starts_from = ends_by + 1
                ends_by = line.index('.tar', starts_from)
                stop_asteroid_number = int(line[starts_from:ends_by])

                result = subprocess.run([self.CMD] + self.CMD_GET_ARGS + [s3_path])
                if not result.returncode:
                    tarfile_name = os.path.basename(s3_path)
                    extract_path = opjoin(self._project_path, self.EXTRACT_ARCHIVE_PATH)
                    symlink_paths = self._make_symlinks_to_files(tarfile_name, extract_path)

                    if not self._find(start_asteroid_number, stop_asteroid_number, phase_storage):
                        continue

                    if not self._plot(start_asteroid_number, stop_asteroid_number, phase_storage,
                                      only_librations):
                        continue

                    self._move_files_to_s3(
                        opjoin(self._project_path, 'output', 'images', '*.png'),
                        opjoin(self._project_path, 'png-%i-%i.tar' %
                               (start_asteroid_number, stop_asteroid_number)),
                        'w', self.S3_PLOTS_DIR)

                    self._clear_phases(start_asteroid_number, stop_asteroid_number)
                    shutil.rmtree(extract_path, True)
                    os.remove(tarfile_name)
                    for item in symlink_paths:
                        os.remove(item)
                    symlink_paths.clear()
                else:
                    self._raw_log('Something wrong during loading %s' % s3_path, False)
                    continue

    def run_full_stack(self, from_day: float, phase_storage: str = 'REDIS',
                       only_librations: bool = False):
        if not self.S3_PLOTS_DIR:
            print('You must to point directory name for plots on AWS S3 (env var AWS_PLOTS_DIR)')
            exit(-1)
        assert self.S3_ROOT_DIR
        _copy_catalog(self._project_path)
        _add_redis_sings(opjoin(self._project_path, 'config', 'local_config.yml'))
        for i in range(self._start, self._stop, self.STEP):
            end = i + self.STEP if i + self.STEP < self._stop else self._stop
            interval = _get_interval(i, end)

            res = subprocess.run([
                opjoin(self._project_path, 'main.py'), '--logfile=%s' % self.CALC_LOGFILE,
                'calc', '--from-day=%s' % from_day, '--to-day=38976000.5'
            ] + interval, cwd=self._project_path, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
            if res.returncode:
                self._handle_process_error(i, end, self.CALC_LOGFILE, res.stderr)
                continue

            if not self._find(i, end, phase_storage):
                continue

            if not self._plot(i, end, phase_storage, only_librations):
                continue

            self._clear_phases(i, end)
            self._move_files_to_s3(
                opjoin(self._project_path, 'mercury', '*.aei'),
                opjoin(self._project_path, 'aei-%i-%i.tar.gz' % (i, end)),
                'w:gz', S3_AEI_FOLDER)
            self._move_files_to_s3(
                opjoin(self._project_path, 'output', 'images', '*.png'),
                opjoin(self._project_path, 'png-%i-%i.tar' % (i, end)),
                'w', self.S3_PLOTS_DIR)

    def run_simple(self, program_args: List[str], need_aei: bool = True):
        _copy_catalog(self._project_path)
        if self._start is not None and self._stop is not None and need_aei:
            _load_aei(self._project_path, self._start, self._stop)
        _add_redis_sings(opjoin(self._project_path, 'config', 'local_config.yml'))
        subprocess.call([opjoin(self._project_path, 'main.py')] + program_args,
                        cwd=self._project_path)
        if need_aei:
            _copy_aei(self._project_path)

    def _make_symlinks_to_files(self, from_archive, extract_path):
        symlink_paths = []
        with tarfile.open(from_archive) as tarf:
            for archive_item in tarf:
                tarf.extract(archive_item, extract_path)
                aei_filename = os.path.basename(archive_item.name)
                aei_filepath = opjoin(extract_path, archive_item.name)
                if aei_filename.endswith('aei'):
                    symlink_path = opjoin(self._project_path, 'mercury', aei_filename)
                    if os.path.exists(symlink_path):
                        os.remove(symlink_path)
                    os.symlink(aei_filepath, symlink_path)
                    symlink_paths.append(symlink_path)
        return symlink_paths

    def _plot(self, start: int, stop: int, phase_storage: str, only_librations: bool):
        interval = _get_interval(start, stop)
        res = subprocess.run([
            opjoin(self._project_path, 'main.py'), '--logfile=%s' % self.PLOT_LOGFILE,
            'plot', '--phase-storage=%s' % phase_storage,
            '--only-librations=%i' % only_librations
        ] + interval, cwd=self._project_path, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if res.returncode:
            self._handle_process_error(start, stop, self.PLOT_LOGFILE, res.stderr)
            return False
        return True

    def _find(self, start: int, stop: int, phase_storage):
        interval = _get_interval(start, stop)
        res = subprocess.run([
            opjoin(self._project_path, 'main.py'), '--logfile=%s' % self.FIND_LOGFILE,
            'find', '--reload-resonances=0', '--phase-storage=%s' % phase_storage
        ] + interval, cwd=self._project_path, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if res.returncode:
            self._handle_process_error(start, stop, self.FIND_LOGFILE, res.stderr)
            return False
        return True

    def _clear_phases(self, start: int, stop: int):
        res = subprocess.run([
            opjoin(self._project_path, 'main.py'), '--logfile=resonances-clear-phases.log',
            'clear-phases', '--start=%s' % start, '--stop=%s' % stop
        ], cwd=self._project_path, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        if res.returncode:
            self._log(start, stop, res.stderr)

    def _raw_log(self, message, save_traceback=True):
        with open(self.LOGFILE, 'a') as f:
            f.write('\n---------\n')
            f.write(message)
            if save_traceback:
                traceback.print_last(file=f)

    def _log(self, start: int, stop: int, message_tail: bytes = None):
        message = 'error during find %i %i\n' % (start, stop)
        if not message_tail:
            self._raw_log(message)
        else:
            self._raw_log("%s%s\n" % (message, message_tail.decode()), False)

    def _handle_process_error(self, start, stop, command_logfile: str, process_stderr: bytes):
        self._log(start, stop, process_stderr)
        self._clear_phases(start, stop)
        logdir = opjoin(self._project_path, 'logs')
        shutil.copy(
            opjoin(logdir, command_logfile),
            opjoin(logdir, command_logfile.replace('.log', '%s-%s.log' % (start, stop)))
        )
        _remove(opjoin(self._project_path, 'output', 'images', '*.png'))
        _remove(opjoin(self._project_path, 'mercury', '*.aei'))

    def has_errors(self):
        return os.path.exists(self.LOGFILE)

    def _move_files_to_s3(self, from_path, archive_path, spec, s3_path: str):
        """
        makes archive, upload it to aws s3, remove archive, remove files.
        :param from_path:
        :param archive_path:
        :param spec:
        :return:
        """
        _archive_plots(archive_path, from_path, spec)
        path = 's3://%s/%s/%s/%s' % (S3_BUCKET_NAME, self.S3_ROOT_DIR, s3_path,
                                     os.path.basename(archive_path))
        res = subprocess.call([self.CMD] + self.CMD_SYNC_ARGS + [archive_path, path])
        if not res:
            try:
                os.remove(archive_path)
            except Exception as e:
                print(e)
        else:
            print('file %s not synced!!!' % archive_path)
        _remove(from_path)


class _ArgParser:
    def __init__(self, cli_args: List[str]):
        self._cli_args = cli_args

    def parse(self, key: str) -> str:
        for item in self._cli_args:
            res = re.match(key, item)
            if res:
                return item[res.end():]
        return None


def main():
    db_is_ready = int(os.environ.get('RESONANCES_DB_READY', 0))
    project_path = os.path.dirname(os.path.abspath(__file__))

    parser = _ArgParser(sys.argv)
    start = None
    stop = None
    except_commands = ['migrate', '--help', 'get_file_list', 'librations']
    if not any([x in sys.argv for x in except_commands]):
        start = int(parser.parse('--start='))
        stop = int(parser.parse('--stop='))

    runner = ProgramRunner(project_path, start, stop)
    if not project_path:
        print('environment variable `project_path` is not set')
        sys.exit(-1)
    if not db_is_ready:
        url = 'postgresql://%s:%s@%s/%s' % _get_signs()
        _edit_config(project_path, url)

        os.environ['RESONANCES_DB_READY'] = '0'
    if 'migrate' in sys.argv:
        subprocess.call(['alembic', 'upgrade', 'head'], cwd=project_path)
    elif 'get_file_list' in sys.argv:
        with open(opjoin(project_path, 'catalog', AWS_S3_AEI_FILE_LIST), 'w') as f:
            subprocess.run([
                's3cmd', '--access_key=%s' % os.environ.get('S3_ACCESS_KEY', ''),
                '--secret_key=%s' % os.environ.get('S3_SECRET_KEY', ''), 'ls',
                's3://%s/%s/%s/' % (S3_BUCKET_NAME, os.environ.get('S3_ROOT_DIR'), S3_AEI_FOLDER)
            ], stdout=f)
    elif 'full_cycle' in sys.argv:
        only_librations = bool(int(parser.parse('--only-librations=')))
        from_day = float(parser.parse('--from-day='))
        phase_storage = parser.parse('--phase-storage=')
        exception_message = ''
        if phase_storage is None:
            exception_message = '--phase-storage %s' % TAIL_MESSAGE
        if from_day is None:
            exception_message += ' --from_day %s' % TAIL_MESSAGE
        if exception_message:
            raise Exception(exception_message)
        runner.run_full_stack(from_day, phase_storage, only_librations)
    elif 'find_plot' in sys.argv:
        only_librations = bool(int(parser.parse('--only-librations=')))
        phase_storage = parser.parse('--phase-storage=')
        exception_message = ''
        if phase_storage is None:
            exception_message = '--phase-storage %s' % TAIL_MESSAGE
        if exception_message:
            raise Exception(exception_message)
        runner.run_find_plot(phase_storage, only_librations)
    else:
        del sys.argv[0]
        runner.run_simple(sys.argv, bool(int(os.environ.get('NEED_AEI', True))))

    if runner.has_errors():
        exit(66)
    exit(0)


if __name__ == '__main__':
    main()
