#!/usr/bin/python2
# -*- coding: utf-8 -*-
from fabric.api import run
from fabric.api import cd
from fabric.api import env
from fabric.api import task
from fabric.api import prefix
from fabric.api import local
from fabric.context_managers import shell_env
from fabric.contrib import files
import os
from fabric.operations import sudo
from os.path import join as opjoin
from six import moves


REPOSITORY_URL = 'https://github.com/4xxi/resonances.git'


@task
def resonances1():
    env.use_ssh_config = True
    env.user = 'deploy'
    env.hosts = ['%s@resonances1.4xxi.com' % env.user]
    env.name = 'resonances1'
    env.root = '/opt/resonances'
    env.activate = 'source ' + os.path.join(env.root, '.venv', 'bin', 'activate')
    env.branch = 'develop'


@task
def clone():
    if not files.exists(env.root):
        sudo('mkdir %s' % env.root)
        sudo('chown %s %s' % (env.user, env.root))
    with cd(env.root):
        run('git clone -b %s %s .' % (env.branch, REPOSITORY_URL))
        run('git submodule update --init')
        with cd(opjoin(env.root, 'mercury')):
            run('./compile.sh')


REMOTE_DUMP_FILENAME = 'fabric-dump.sql.gz'


@task
def backup():
    def _get_db_parameters():
        fd = moves.StringIO()
        files.get(os.path.join(env.root, 'alembic.ini'), fd)
        content = fd.getvalue()
        urlparameter = [x for x in content.split('\n') if x.startswith('sqlalchemy.url')][0]

        dbpath = urlparameter.split()[2]
        dbpars = moves.urllib.parse.urlparse(dbpath).netloc

        dbname = moves.urllib.parse.urlparse(dbpath).path[1:]
        username = dbpars.split(':')[0]
        host = dbpars.split('@')[1]
        password = dbpars.split(':')[1].split('@')[0]

        return username, host, dbname, password

    username, host, dbname, password = _get_db_parameters()
    with shell_env(fabric='true', PGPASSWORD=password):
        with cd(env.root):
            cmd = "pg_dump --host=%s --username=%s %s | gzip > %s" % (
                host, username, dbname, REMOTE_DUMP_FILENAME)
            with prefix(env.activate):
                run(cmd)


@task
def make_venv():
    with cd(env.root):
        run('virtualenv .venv --python=/usr/bin/python3.5')


@task
def install_deps():
    with cd(env.root):
        if not files.exists('.venv'):
            make_venv()

        with prefix(env.activate):
            run("pip install -r reqs.pip")


@task
def get_catalog():
    path = opjoin(env.root, 'catalog')
    if not files.exists(path):
        run('mkdir %s' % path)
    run('wget -O %s http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat' %
        opjoin(path, 'allnum.cat'))


@task
def get_resonances():
    path = opjoin(env.root, 'axis')
    if not files.exists(path):
        run('mkdir %s' % path)
    url = 'https://raw.githubusercontent.com/smirik/Three-body-resonances/master/axis/resonances'
    run('wget -O %s %s' % (opjoin(path, 'resonances'), url))


@task
def initdb(username, password, host, dbname):
    with cd(env.root):
        run("psql -c 'create database %s' -U %s -d postgres" % (dbname, username))
        path = opjoin(env.root, 'alembic.ini')
        if not files.exists(path):
            run('cp alembic.ini.dist %s' % path)

        if files.contains(path, '# sqlalchemy.url'):
            url = 'postgresql://%s:%s@%s/%s' % (username, password, host, dbname)
            files.sed(path, '^# sqlalchemy.url(.*)', 'sqlalchemy.url = %s' % url)


@task
def migrate():
    with cd(env.root):
        with prefix(env.activate):
            run('alembic upgrade head')


@task
def calc():
    with cd(env.root):
        with prefix(env.activate):
            run('python ./main.py calc')


@task
def find():
    with cd(env.root):
        with prefix(env.activate):
            run('python ./main.py find')


@task
def update():
    local("git push origin %s" % env.branch)
    with cd(env.root):
        run("git checkout %s" % env.branch)
        run("git pull origin %s" % env.branch)


@task
def setup_deploy(username, password, host, dbname):
    clone()
    install_deps()
    initdb(username, password, host, dbname)
    migrate()
    get_catalog()
    get_resonances()


@task
def deploy():
    update()
    backup()
    install_deps()
    migrate()

