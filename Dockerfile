FROM python:3.5.1
RUN apt-get update && apt-get install -y \
        #python3 python3-pip \
        gfortran gnuplot wget git libpq-dev sed \
        && mkdir -p /opt/resonances/mercury \
        && mkdir /opt/catalog \
        && wget 'http://hamilton.dm.unipi.it/~astdys2/catalogs/allnum.cat' -O /opt/catalog/allnum.cat

ADD ./mercury /opt/resonances/mercury
ADD ./reqs.pip /opt/resonances/reqs.pip

RUN pip install -r /opt/resonances/reqs.pip && pip install awscli==1.10.23

RUN cd /opt/resonances/mercury/ && ./compile.sh \
        && apt-get remove -y gfortran && apt-get autoclean -y && apt-get autoremove -y

WORKDIR /opt/resonances/

ADD . /opt/resonances/

ENTRYPOINT ["/opt/resonances/main.py"]
