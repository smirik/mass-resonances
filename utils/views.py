from settings import Config
import os
from os.path import join as opjoin

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()
OUTPUT_GNU_PATH = opjoin(PROJECT_DIR, CONFIG['output']['gnuplot'])
OUTPUT_RES_PATH = opjoin(PROJECT_DIR, CONFIG['output']['angle'])


def create_gnuplot_file(body_number):
    with open(os.path.join(PROJECT_DIR, 'output', 'multi.gnu')) as gnuplot_sample_file:
        content = gnuplot_sample_file.read()

    content = (
        content.replace('result', '%s/A%i.res' % (OUTPUT_RES_PATH, body_number))
        .replace('set xrange [0:100000]', 'set xrange [0:%i]' % CONFIG['gnuplot']['x_stop'])
        .replace('with points', 'with %s' % CONFIG['gnuplot']['type'])
    )

    if not os.path.exists(OUTPUT_GNU_PATH):
        os.makedirs(OUTPUT_GNU_PATH)

    path = opjoin(OUTPUT_GNU_PATH, 'A%i.gnu' % body_number)
    with open(path, 'w+') as gnuplot_file:
        gnuplot_file.write(content)
    return path
