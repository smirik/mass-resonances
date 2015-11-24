from settings import Config
import os

CONFIG = Config.get_params()
PROJECT_DIR = Config.get_project_dir()


def create_gnuplot_file(body_number):
    output_gnu = CONFIG['output']['gnuplot']
    output_res = CONFIG['output']['angle']

    gnuplot_sample_file = open(os.path.join(
        PROJECT_DIR, 'output', 'multi.gnu'))
    content = gnuplot_sample_file.read()

    content = (
        content.replace('result', '%s/A%i.res' % (output_res, body_number))
        .replace('set xrange [0:100000]', 'set xrange [0:%i]' % CONFIG['gnuplot']['x_stop'])
        .replace('with points', 'with %s' % CONFIG['gnuplot']['type'])
    )

    gnuplot_file = open(os.path.join(
        PROJECT_DIR, output_gnu, 'A%i.gnu' % body_number
    ), 'w+')
    gnuplot_file.write(content)

    gnuplot_sample_file.close()
    gnuplot_file.close()
