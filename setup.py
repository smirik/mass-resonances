from distutils.core import setup

setup(
    name='resonances',
    version='0.1.0',
    packages=['resonances', 'resonances.cli', 'resonances.view', 'resonances.catalog',
              'resonances.commands', 'resonances.commands.reports',
              'resonances.commands.fileoperations', 'resonances.entities',
              'resonances.entities.libration', 'resonances.entities.resonance',
              'resonances.datamining', 'resonances.datamining.librations',
              'resonances.datamining.orbitalelements', 'resonances.integrator'],
    url='',
    license='',
    author='4xxi',
    author_email='am@4xxi.com',
    description='Application for integration two and three body resonances.',
    install_requires=[
        'PyYAML==3.11',
        'click==5.1',
        'SQLAlchemy==1.0.9',
        'alembic==0.8.3',
        'psycopg2==2.6.1',
        'redis==2.10.5',
        'texttable==0.8.4',
        'boto==2.41.0',
        'numpy==1.10.4',
        'beautifulsoup4==4.5.1',
    ],
)
