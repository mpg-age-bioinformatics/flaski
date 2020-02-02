# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
FROM flaski/debian

LABEL maintainer "bioinformatics@age.mpg.de"

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq redis-server && \
apt-get clean && rm -rf /var/lib/apt/lists/*

# data folders
RUN mkdir -p /faski_data/redis

EXPOSE 6379

ENTRYPOINT /bin/bash -c 'redis-server redis.conf --requirepass $REDIS_PASSWORD'

# docker build -t flaski/redis .
# docker run -d -e REDIS_PASSWORD=REDIS_PASSWORD --name redis -it flaski/redis