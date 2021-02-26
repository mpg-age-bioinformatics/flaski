# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.
FROM flaski/flaski:1.7.2

USER root

RUN mkdir /submissions
RUN chown -R flaski:flaski /submissions

# remove old flaski files
RUN rm -rf /flaski

# data folders and access rights
RUN mkdir -p /var/log/flaski /flaski/.git /flaski/data /flaski/flaski /flaski/migrations /flaski/utils /flaski/services /flaski/pyflaski /flaski_data/users /backup/users_data /backup/mariadb
RUN touch /mysql_backup.log && touch /rsync.log
RUN chown -R flaski:flaski /flaski_data /flaski_data/users /flaski/migrations /var/log/flaski /mysql_backup.log /rsync.log

# comment during development
COPY requirements.txt /flaski/
RUN pip3 install -r /flaski/requirements.txt

COPY LICENSE.md README.md config.py flaski.py MANIFEST.in requirements.txt setup.py .flaskenv /flaski/
COPY pyflaski /flaski/pyflaski
COPY services /flaski/services
COPY utils /flaski/utils
COPY flaski /flaski/flaski
COPY data /flaski/data
COPY .git /flaski/.git

# Setup default user, when enter docker container
USER flaski:flaski
WORKDIR /flaski

ENTRYPOINT /flaski/services/server/docker-entrypoint.sh