import logging
import subprocess
import os
from os.path import join as opjoin


from mercury_bridge import calc
from utils import ResonanceDatabase
from settings import ConfigSingleton
from settings import PROJECT_DIR
from mercury_bridge.programms import simple_clean
from mercury_bridge.programms import element6

CONFIG = ConfigSingleton.get_singleton()


def extract(start: int, elements: bool = False, do_copy_aei: bool = False) -> bool:
    """Extract resonance file from archive to directory in export folder
    start — first object number for extracting (start + number of bodies)
    elements — should mercury6 create aei files for all objects?

    :param start int:
    :param elements bool:
    :param do_copy_aei bool:
    :rtype bool:
    :return:
    """
    # Start should have 0 remainder to number of bodies because of structure
    num_b = int(CONFIG['integrator']['number_of_bodies'])
    start -= start % num_b

    # Check directory in aei export archive
    body_number_stop = start + num_b
    aei_dir = opjoin(PROJECT_DIR, CONFIG['export']['aei_dir'],
                     start, body_number_stop, 'aei')

    if os.path.exists(opjoin(aei_dir, 'A%i.aei' % start)):
        return True

    end = start + num_b
    export_base_dir = opjoin(PROJECT_DIR, CONFIG['export']['base_dir'])

    export_dir = opjoin(export_base_dir, '%i-%i' % (start, end))
    tar_file = 'integration%i-%i.tar.gz' % (start, end)
    export_tar = opjoin(export_base_dir, tar_file)

    if not os.path.exists(export_dir):
        logging.debug('Directory %s directory not exists.' % export_dir)
        logging.debug('Trying to find archive and extract...')

        if os.path.exists(export_tar):
            code = subprocess.call(['tar', '-xf', tar_file],
                                   cwd=opjoin(export_base_dir))
            if code:
                raise Exception('Error during unpacking arhive %s' % tar_file)
            logging.debug('[done]')
        else:
            logging.error('Archive %s not found')
            return False

    def _copy_integrator_files():
        logging.debug('Copy integrator files... ')
        res = subprocess.call([
            'cp', opjoin(PROJECT_DIR, export_dir, 'mercury', '*'),
            opjoin(PROJECT_DIR, 'mercury')
        ])
        if res:
            raise Exception('Something wrong during copy')
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
        code = subprocess.call([
            'cp', opjoin(PROJECT_DIR, export_dir, 'aei', '*'),
            opjoin(PROJECT_DIR, 'mercury')
        ])
        if code:
            raise Exception('Something wrong during copy')
        logging.debug('[done]')

        if not os.path.exists(aei_filename):
            logging.warning('AEI files not found')
            logging.debug('Creating aei files... ')
            element6()
            logging.debug('[done]')

    if do_copy_aei:
        logging.info('Copy AEI files to export directory')
        for i in range(100):
            source = opjoin(PROJECT_DIR, 'mercury', 'A%i.aei' % (start + i))
            target = opjoin(PROJECT_DIR, export_dir, 'aei')
            code = subprocess.call(['cp', source, target])
            if code:
                raise Exception('Something wrong during copy %s to %s' %
                                (source, target))

    return True


def calc_resonances(start: int, stop: int = None, elements: bool = False):
    """Calculate resonances and plot the png files for given object

    :param start int:
    :param stop int:
    :param elements bool:
    """

    def _max() -> int:
        return 1

    num_b = CONFIG['integrator']['number_of_bodies']

    output_gnu = CONFIG['output']['gnuplot']
    output_images = CONFIG['output']['images']

    rdb = ResonanceDatabase('export/full.db')

    if not stop:
        stop = start + int(num_b)

    asteroids = rdb.find_between(start, stop)

    # Extract from archive data
    is_extracted = extract(start, elements)

    for asteroid in asteroids:
        asteroid_num = str(asteroid.number)
        logging.info('Plot for asteroid # %s' % asteroid_num)
        calc(asteroid_num, asteroid.resonance)
        has_circulation = Series.findCirculation(asteroid_num, 0, CONFIG['gnuplot']['x_stop'], false, true)
        if has_circulation:
            # max = Series.max(has_circulation[0])
            max = _max()
            logging.info("% = %s%, medium period = %s, max = %s" % (
                has_circulation[1],
                has_circulation[2],
                max
            ))
        else:
            logging.info("pure resonance")

            # View.createGnuplotFile(asteroid_num)
            # tmp = %x[ gnuplot #{output_gnu}/A#{asteroid_num}.gnu > #{output_images}/A#{asteroid_num}.png ]
