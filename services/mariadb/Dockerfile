# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
FROM flaski/debian

LABEL maintainer "bioinformatics@age.mpg.de"

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq mariadb-server mariadb-client && \
apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 3306

COPY mysql.sh /mysql.sh

RUN cp -rp /var/lib/mysql /var/lib/mysql_

ENTRYPOINT /bin/bash -c 'cd /var/lib/mysql_/ && \
for f in $(ls) ; do \
  if [[ ! -e /var/lib/mysql/${f} ]] ; \
    then mv /var/lib/mysql_/${f} /var/lib/mysql/${f}; NEWSTART="TRUE" ; \
  fi \
done \
&& service mysql start \
&& sleep 2 \
&& if [[ "${NEWSTART}" == "TRUE"  ]] ; then source /mysql.sh && sleep 5 && service mysql restart ; fi \
&& cd / && /bin/bash'

# docker build -t flaski/mariadb . 
# docker run -d \
# -v ~/flaski_data/mariadb:/var/lib/mysql
# -e myqsl_password=sqpass \
# -e MAINDB=flaski \
# -e PASSWDDB=flaskidbpass \
# --name mariadb -it flaski/mariadb

# docker run -d -v ~/flaski_data/mariadb:/var/lib/mysql -e myqsl_password=sqpass -e MAINDB=flaski -e PASSWDDB=flaskidbpass --name mariadb -it flaski/mariadb