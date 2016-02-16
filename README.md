* Master: [![Build Status](https://travis-ci.org/4xxi/resonances.svg?branch=master)](https://travis-ci.org/4xxi/resonances)
* Develop: [![Build Status](https://travis-ci.org/4xxi/resonances.svg?branch=develop)](https://travis-ci.org/4xxi/resonances)

# resonances
This is Python fork of Three-body-resonances (https://github.com/smirik/Three-body-resonances).

# Installation
* virtualenv .venv
* source .venv/bin/activate
* pip install -r reqs.pip
* If it needs, you can override settings by file config/local_config.yml
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
* redis

# Deploy via fabric

...

# Run

To run the script on the server please follow the instructions below:

1. Run the script: `source .venv/bin/activate`
2. Run the calc command: `./main.py calc`
3. To find the resonances: `./main.py find`
4. Make plots `./main.py plot`

# pylint cheat sheet
pylint -E `git ls | grep py$ | grep -v --regexp="\(alembic\|fabfile\.py\)"` --disable=E1136 --disable=E1126

# Default integrator Mercury parameters for out purposes.
Take a look on files param.in, big.in, small.in.

* `param.in` must contain algorithm `mvs`. `Start time` must be `2451000.5` and `stop time` must be
`38976000.5`, they passed by arguments for `calc` command. Make `./main.py calc --help` for more.
* `big.in` must contain `epoch` that equals `2451000.5`.
* `small.in` lists asteroids. For every asteroid it stores `ep` (means epoch), this parameter must
be `2455400.5`. This day is result of expression `55400.0 + 2400000.5`, where `55400.0` has been got
from astdys catalog (allnum.cat). This value must be changed in config.yml if you have different value
in catalog.