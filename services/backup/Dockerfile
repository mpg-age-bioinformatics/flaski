# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

FROM mariadb/server

LABEL maintainer "bioinformatics@age.mpg.de"

RUN mkdir -p /backups/mariadb /backups/users /flaski_data/users 

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq cron && \
apt-get clean && rm -rf /var/lib/apt/lists/*

COPY run-backups.sh /run-backups.sh

COPY cron.job /cron.job

RUN crontab /cron.job