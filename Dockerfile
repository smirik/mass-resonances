FROM python:3.5.1
RUN apt-get update && apt-get install -y \
        gfortran gnuplot wget git libpq-dev sed \
        && mkdir -p /opt/resonances/mercury \
        && mkdir /opt/resonances/catalog


ADD ./mercury /opt/resonances/mercury
ADD ./catalog/allnum.cat.gz /opt/resonances/catalog/
ADD ./reqs.txt /opt/resonances/
RUN pip install -r /opt/resonances/reqs.txt

RUN cd /opt/resonances/mercury/ && ./compile.sh \
        && cd /opt/resonances/catalog/ && gunzip allnum.cat.gz \
        && apt-get remove -y gfortran && apt-get autoclean -y && apt-get autoremove -y \
        && apt-get install libgfortran3

WORKDIR /opt/resonances/

ADD . /opt/resonances/
RUN pip install /opt/resonances/


ENTRYPOINT ["/opt/resonances/main.py"]
