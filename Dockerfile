FROM python:3.5.1
RUN apt-get update && apt-get install -y \
        #python3 python3-pip \
        gfortran gnuplot wget git libpq-dev sed \
        && mkdir -p /opt/resonances/mercury

ADD ./mercury /opt/resonances/mercury
ADD ./reqs.pip /opt/resonances/reqs.pip

RUN cd /opt/resonances/mercury/ && ./compile.sh && pip install -r /opt/resonances/reqs.pip \
        && apt-get remove -y gfortran && apt-get autoclean -y && apt-get autoremove -y \
        && mkdir /opt/catalog \
        && wget 'http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat' -O /opt/catalog/allnum.cat

WORKDIR /opt/resonances/

ADD . /opt/resonances/

ENTRYPOINT ["/opt/resonances/entrypoint.py"]
