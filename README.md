* Master: [![Build Status](https://travis-ci.org/4xxi/resonances.svg?branch=master)](https://travis-ci.org/4xxi/resonances)
* Develop: [![Build Status](https://travis-ci.org/4xxi/resonances.svg?branch=develop)](https://travis-ci.org/4xxi/resonances)

# resonances
This is Python fork of Three-body-resonances (https://github.com/smirik/Three-body-resonances).

# Installation
* virtualenv .venv
* source .venv/bin/activate
* pip install -r reqs.pip
* move alembic.ini.dist alembic.ini and point in this file path to database in parameter 
`sqlalchemy.url` in section `[alembic]`

# Requirements
* postgresql 9.4
* python 3.5
* pip 7.1.2
* gfortran
* gnuplot
* wget
* git
* python-virtualenv
* libpq-dev
* libpython3.5-dev
* sed

# Deploy via fabric

...

# Run

To run the script on the server please follow the instructions below:

1. Run the script: `source .venv/bin/activate`
2. Run the calc command: `./main.py calc`
3. To find the resonances: `./main.py find`

# pylint cheat sheet
pylint -E `git ls | grep py$ | grep -v --regexp="\(alembic\|fabfile\.py\)"` --disable=E1136 --disable=E1126
