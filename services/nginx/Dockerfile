# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
FROM flaski/debian

LABEL maintainer "bioinformatics@age.mpg.de"

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq nginx && \
apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 80
EXPOSE 443

RUN mkdir -p /flaski_data/certificates /flaski_data/logs && rm /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
COPY flaski.conf /etc/nginx/sites-enabled/flaski.conf
COPY flaski.conf /etc/nginx/sites-available/flaski.conf

ENTRYPOINT /bin/bash -c 'service nginx reload && /etc/init.d/nginx start

# docker build -t flaski/nginx .
# docker run -d \
# -v ~/flaski_data/certificates:/flaski_data/certificates \
# -v ~/flaski_data/logs:/flaski_data/certificates \
# --name nginx -it flaski/nginx