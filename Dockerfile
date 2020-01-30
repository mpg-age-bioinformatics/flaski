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
apt-get install -yq python3 python3-pip && \
apt-get install -yq redis-server && \
apt-get clean && rm -rf /var/lib/apt/lists/* && \
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

ENV SHELL /bin/bash
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

RUN mkdir -p /flaski /faski_data/data /faski_data/redis /faski_data/users /faski_data/logs

COPY requirements.txt .

RUN pip3 install -r requirements.txt

# Jupyter port
EXPOSE 8888
# Flask
EXPOSE 5000

WORKDIR /flaski

ENTRYPOINT /bin/bash -c '\
if [[ "$FLASK_ENV" == "development" ]] ; \
 then \
 python3 -m smtpd -n -c DebuggingServer localhost:8025 & \
fi ; \
redis-server redis.conf --daemonize yes &&  flask run --host 0.0.0.0'