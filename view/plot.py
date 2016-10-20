import subprocess

import os
from settings import Config

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


def make_plot(res_filename: str, gnu_filepath: str, png_filename: str, title: str = ''):
    _create_gnuplot_file(res_filename, gnu_filepath, title)
    with open(png_filename, 'wb') as image_file:
        subprocess.call(['gnuplot', gnu_filepath], stdout=image_file)


def _create_gnuplot_file(res_filepath, gnu_filepath, title: str):
    with open(os.path.join(PROJECT_DIR, 'view', 'multi.gnu')) as gnuplot_sample_file:
        content = gnuplot_sample_file.read()

    content = (
        content.replace('result', res_filepath)
        .replace('set xrange [0:100000]', 'set xrange [0:%i]' % CONFIG['gnuplot']['x_stop'])
        .replace('with points', 'with %s' % CONFIG['gnuplot']['type'])
        .replace('set label ""', 'set label "%s"' % title)
    )

    with open(gnu_filepath, 'w+') as gnuplot_file:
        gnuplot_file.write(content)
