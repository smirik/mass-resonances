import glob
import logging
import subprocess

import os
import shutil
from integrator.programs import element6
from integrator.programs import simple_clean
from os.path import join as opjoin
from settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
BODIES_COUNTER = int(CONFIG['integrator']['number_of_bodies'])
EXPORT_BASE_DIR = opjoin(PROJECT_DIR, CONFIG['export']['base_dir'])


class ExtractError(Exception):
    pass


def extract(start: int, elements: bool = False, do_copy_aei: bool = False) -> bool:
    """Extract resonance file from archive to directory in export folder
    start — first object number for extracting (start + number of bodies)
    elements — should mercury6 create aei files for all objects?

    :param int start:
    :param bool elements:
    :param bool do_copy_aei:
    :rtype bool:
    :raises FileNotFoundError: if archive not found.
    :return:
    """
    # Start should have 0 remainder to number of bodies because of structure
    start -= start % BODIES_COUNTER - 1

    # Check directory in aei export archive
    end = start + BODIES_COUNTER
    aei_dir = opjoin(PROJECT_DIR, CONFIG['export']['aei_dir'],
                     '%i-%i' % (start, end), 'aei')

    if os.path.exists(opjoin(aei_dir, 'A%i.aei' % start)):
        return True

    export_dir = opjoin(EXPORT_BASE_DIR, '%i-%i' % (start, end))
    tar_file = 'integration%i-%i.tar.gz' % (start, end)
    export_tar = opjoin(EXPORT_BASE_DIR, tar_file)

    if not os.path.exists(export_dir):
        logging.debug('Directory %s directory not exists.' % export_dir)
        logging.debug('Trying to find archive and extract...')

        if os.path.exists(export_tar):
            code = subprocess.call(['tar', '-xf', tar_file],
                                   cwd=opjoin(EXPORT_BASE_DIR))
            if code:
                logging.error('Error during unpacking arhive %s' % tar_file)
                return False
            else:
                logging.debug('[done]')
        else:
            e = FileNotFoundError('Archive %s not found' % export_tar)
            e.filename = export_tar
            raise e

    def _copy_files_from_export_dir(from_dir: str):
        for item in glob.iglob(opjoin(PROJECT_DIR, export_dir, from_dir, '*')):
            shutil.copy(item, opjoin(PROJECT_DIR, 'mercury'))

    def _copy_integrator_files():
        logging.debug('Copy integrator files... ')
        _copy_files_from_export_dir('mercury')
        logging.debug('[done]')

    if elements:
        logging.debug('Clean integrator directory...')
        simple_clean()
        logging.debug('[done]')

        _copy_integrator_files()

        logging.debug('Creating aei files... ')
        element6()
        logging.debug('[done]')

    # Check aei files in mercury directory
    # @todo diff integrators
    aei_filename = opjoin(PROJECT_DIR, CONFIG['integrator']['dir'],
                          'A%i.aei' % start)
    if not elements and not os.path.exists(aei_filename):
        _copy_integrator_files()

        # Copy aei files if exists
        logging.debug('Copy aei files... ')
        _copy_files_from_export_dir('aei')
        logging.debug('[done]')

        if not os.path.exists(aei_filename):
            logging.warning('AEI files not found')
            logging.debug('Creating aei files... ')
            element6()
            logging.debug('[done]')

    if do_copy_aei:
        logging.info('Copy AEI files to export directory')
        for i in range(BODIES_COUNTER):
            source = opjoin(PROJECT_DIR, 'mercury', 'A%i.aei' % (start + i))
            target = opjoin(PROJECT_DIR, export_dir, 'aei')
            code = subprocess.call(['cp', source, target])
            if code:
                raise Exception('Something wrong during copy %s to %s' %
                                (source, target))

    return True
