# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
FROM debian@sha256:11253793361a12861562d1d7b15b8b7e25ac30dd631e3d206ed1ca969bf97b7d

LABEL maintainer "bioinformatics@age.mpg.de"

USER root

ENV DEBIAN_FRONTEND noninteractive

RUN echo "deb http://ftp.debian.org/debian buster main non-free contrib" >> /etc/apt/sources.list && \
echo "deb-src http://ftp.debian.org/debian buster main non-free contrib" >> /etc/apt/sources.list && \
echo "deb http://ftp.debian.org/debian buster-updates main contrib non-free" >> /etc/apt/sources.list && \
echo "deb-src http://ftp.debian.org/debian buster-updates main contrib non-free" >> /etc/apt/sources.list && \
echo "deb http://cdn-fastly.deb.debian.org/debian buster main\ndeb http://cdn-fastly.deb.debian.org/debian-security buster/updates main" > /etc/apt/sources.list

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq --no-install-recommends locales && \
apt-get clean && rm -rf /var/lib/apt/lists/* && \
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

ENV SHELL /bin/bash
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq python3 python3-pip libcairo2-dev pkg-config python3-dev mariadb-client && \
apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install pymysql

# data folders
RUN mkdir -p /flaski/ /faski_data/users /faski_data/logs

#comment during development
#COPY * /flaski/

COPY requirements.txt /flaski/
RUN pip3 install -r /flaski/requirements.txt

# Jupyter port
EXPOSE 8888
# Flask
EXPOSE 8000

WORKDIR /flaski

ENTRYPOINT /bin/bash -c '/flaski/services/server/docker-entrypoint.sh ; bin/bash'