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

For more details invoke --help or see [Usage](#usage)

# Run over Docker

The application also available over docker. Image for docker container is
[here](https://hub.docker.com/r/amarkov/resonances/). It contains reference how to launch Resonances
over container. Commonly it is very similar, but instead `main.py` you need `docker run --rm
--volumes-from=resonances-data-container --link resonances-data-container:postgres
--link some-redis:redis --name resonances -e RESONANCES_DB_NAME=resonances
-e RESONANCES_DB_USER=postgres amarkov/resonances` after name of image `amarkov/resonances`
container takes arguments for the application. If you type `--help` in tail (`docker run -it --rm
--volumes-from=resonances-data-container --link resonances-data-container:postgres
--link some-redis:redis --name resonances -e RESONANCES_DB_NAME=resonances
-e RESONANCES_DB_USER=postgres amarkov/resonances --help`) you will get help message of the
application, that also in [Usage](#usage) section.

What about another parameters before image's name?
---
* `run` means launch container. If image, that pointed in tail, doesn't exist on computer, it will be loaded.
* `--rm` means, that Docker will remove container after finishing process. E. g. if you invoke `--help`
of the application, this shows you help message, after this container will be removed. It is not required,
it is just for convinient. If you don't point this flag, you will remove container manually, when it will be need.
* `--volumes-from=resonances-data-container` this marks, that volumes will be mounted from container
`resonances-data-container`. This container must be launched before our target container and it must work
all time. It contains Postgresql and volumes, that stores output data of the application.
* `--link resonances-data-container:postgres` again `resonances-data-container`. This shows, that our container
will be linked to this container. `postgres` just alias of link. The application's container also 
will get environment variables of `resonances-data-container`.
* `--link some-redis:redis` same as above point.
* `--name resonances` sets name for our container. This values must be unique.
* `-e RESONANCES_DB_NAME=resonances` sets environment variable `RESONANCES_DB_NAME`. By default
`resonances-data-container` has database `resonances` and it is need to point this to the container
of our application.
* `-e RESONANCES_DB_USER=postgres` same as above point.
* `amarkov/resonances` name of images, that will be loaded from hub.docker.com, if you don't have it.



# pylint cheat sheet
``pylint -E `git ls | grep py$ | grep -v --regexp="\(alembic\|fabfile\.py\)"` --disable=E1136 --disable=E1126``

# Default integrator Mercury parameters for our purposes.
Take a look on files param.in, big.in, small.in.

* `param.in` must contain algorithm `mvs`. `--from-day` must be `2451000.5` and `--to-day` must be
`38976000.5`, they passed by arguments for `calc` command. Make `./main.py calc --help` for more.
* `big.in` must contain `epoch` that equals `2451000.5`.
* `small.in` lists asteroids. For every asteroid it stores `ep` (means epoch), this parameter must
be `2455400.5`. This day is result of expression `55400.0 + 2400000.5`, where `55400.0` has been got
from astdys catalog (allnum.cat). This value must be changed in config.yml if you have different value
in catalog.

# <a href="usage"></a>Usage

**Usage: main.py calc [OPTIONS]**

```
  Launch integrator Mercury6 for computing orbital elements of asteroids and
  planets, that will be stored in aei files.

Options:
  --start INTEGER   Start asteroid number. Counting from 1.
  --stop INTEGER    Stop asteroid number. Excepts last. Means, that asteroid
                    with number, that equals this parameter, will not be
                    integrated.
  --from-day FLOAT  This parameter will be passed to param.in file for
                    integrator Mercury6 as start time pointed in days.
  --to-day FLOAT    This parameter will be passed to param.in file for
                    integrator Mercury6 as stop time pointed in days.
  --help            Show this message and exit.
```
  
**Usage: main.py find [OPTIONS]**

```
  Computes resonant phases, find in them circulations and saves to
  librations. Parameters --from-day and --to-day are use only --recalc
  option is true.

Options:
  --start INTEGER              Start asteroid number. Counting from 1.
  --stop INTEGER               Stop asteroid number. Excepts last. Means, that
                               asteroid with number, that equals this
                               parameter, will not be integrated.
  --from-day FLOAT             This parameter will be passed to param.in file
                               for integrator Mercury6 as start time pointed
                               in days.
  --to-day FLOAT               This parameter will be passed to param.in file
                               for integrator Mercury6 as stop time pointed in
                               days.
  --reload-resonances BOOLEAN  If true, the application will load integers,
                               satisfying D'Alamebrt rule, from /media/storage
                               /develop/resonances/axis/resonances.
  --recalc BOOLEAN             If true, the application will invoke calc
                               method before
  --is-current BOOLEAN         If true, the application will librations only
                               from database, it won't compute them from
                               phases
  --migrate-phases BOOLEAN     will loads phases to postgres from redis
  --help                       Show this message and exit.
```
  
**Usage: main.py plot [OPTIONS]**

```
Build graphics for asteroids in pointed interval, that have libration.
  Libration can be created by command 'find'.

Options:
  --start INTEGER    Start asteroid number. Counting from 1.
  --stop INTEGER     Stop asteroid number. Excepts last. Means, that asteroid
                     with number, that equals this parameter, will not be
                     integrated.
  --from-db BOOLEAN  If true, applicatioin will loads resonant phases from
                     database instead redis.
  --help             Show this message and exit.
```
