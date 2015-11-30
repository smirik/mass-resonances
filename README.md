[![Build Status](https://travis-ci.org/smirik/resonances.svg?branch=master)](https://travis-ci.org/smirik/resonances)
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
