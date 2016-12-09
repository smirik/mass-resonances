#!/bin/bash

wget ftp://ftp.dante.de/pub/tex/graphics/gnuplot/5.0.5/gnuplot-5.0.5.tar.gz &&\
    tar -zvxf gnuplot-5.0.5.tar.gz && cd gnuplot-5.0.5 &&\
    ./configure && make && make install
