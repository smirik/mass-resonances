# Architecture of the application
Application has 9 modules.

* CLI — makes interface for user it calls scenarios from Commands module.
* Commands — contains different scenarios, that depends on 4 below modules.
* Datamining — module is responsible for mining data and building structures from it.
* Catalog — allows to work with catalog of asteroids.
* Integrator — is responsible for running application mercury6.
* View — represents data in plots. In future will make reports.
* Shortcuts — contains cross module reusable methods.
* Entities — module contains representations and utilities for working with database and Redis.
* Settings — collect settings for running the application and unit tests.

![Package diagram](https://raw.githubusercontent.com/4xxi/resonances/feature/documentation/docs/package.jpeg)

# Running tests and coverage
For running tests you need [pytest](http://pytest.org/latest/) and [coverage](https://github.com/nedbat/coveragepy)

* Run tests `coverage run --omit='./.venv/*,./tests/*' -m pytest -vv ./tests/**/*.py -s`
* Get report `coverage report`

# Database relational model
![Relational model](https://raw.githubusercontent.com/4xxi/resonances/feature/documentation/docs/db.jpg)

* planet — table contains integers, satisfying D'Alambert rule for longitude and perihellion
longitude, name of planet
* asteroid — table contains integers, satisfying D'Alambert rule for longitude and perihellion
longitude, name of asteroid and semi major axis, that uses for comparing with semi major axis from
catalog.
* resonance — table aggregates asteroid and planets to set of integers, satisfying D'Alambert rule.
* phase — contains resonant phases related to resonance. It represents by year and value in
interval from `-Pi` to `Pi`.
* libration — contains info about vector of phases. Column `average_delta` contains average of
differences of neighbor resonant phases. Column `circulation_breaks` contains vector of years, when
some neighbor resonant phases has difference more than `Pi`.
Column `percentage` contains ratio of differences between neighbor breaks, that are
more that option `resonance.libration.min`, represented in percents. Column `is_apocentric`
indicates that resonant phases have been shifted `Pi`.
* broken_asteroid — contains names of asteroids, that have broken aei data.
* alembic_version — contains migrations.
