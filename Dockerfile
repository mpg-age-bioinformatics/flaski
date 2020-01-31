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
apt-get install -yq libcairo2-dev pkg-config python3-dev && \
apt-get clean && rm -rf /var/lib/apt/lists/* && \
echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && locale-gen

## mysql
RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq mariadb-server mariadb-client postfix supervisor nginx git && \
apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install pymysql

ENV SHELL /bin/bash
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# data folders
RUN mkdir -p /flaski /faski_data/data /faski_data/redis /faski_data/users /faski_data/logs /flaski_data/certificates

# python requirements
COPY requirements.txt .

RUN pip3 install -r requirements.txt

# Jupyter port
EXPOSE 8888
# Flask
EXPOSE 5000
EXPOSE 8080
EXPOSE 8041

WORKDIR /flaski

### mysql
# password for mysql
ENV myqsl_password=sqpass

# user and password for the database used by flaski
ENV MAINDB=flaski
ENV PASSWDDB=flaskidbpass

COPY mysql_secure_installation.sh /tmp/mysql_secure_installation.sh

RUN /bin/bash -c 'service mysql start && \
chmod +x /tmp/mysql_secure_installation.sh && \
/tmp/mysql_secure_installation.sh && \
rm -rf /tmp/mysql_secure_installation.sh'

### nginx
RUN rm /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
COPY flaski.conf /etc/nginx/sites-enabled/flaski.conf
COPY flaski.conf /etc/nginx/sites-available/flaski.conf

ENTRYPOINT /bin/bash -c '\
if [[ "$FLASK_ENV" == "development" ]] ; \
 then \
 python3 -m smtpd -n -c DebuggingServer localhost:8025 & \
fi && \
service mysql restart && service nginx reload && /etc/init.d/nginx start && redis-server redis.conf --daemonize yes && \
if [[ "$FLASK_ENV" != "development" ]] ; \
 then \
 gunicorn -b localhost:8000 -w 4 flaski:app & \
else /etc/init.d/nginx stop && flask run --host 0.0.0.0 & \
fi && \
/bin/bash'