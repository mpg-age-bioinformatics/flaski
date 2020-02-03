# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
#FROM flaski/debian

FROM mariadb/server

LABEL maintainer "bioinformatics@age.mpg.de"

# RUN apt-get update && apt-get -yq dist-upgrade && \
# apt-get install -yq mariadb-server mariadb-client && \
# apt-get clean && rm -rf /var/lib/apt/lists/*

# EXPOSE 3306

# COPY mysql.sh /mysql.sh

# RUN sed -i 's/bind-address/#bind-address/g' /etc/mysql/mariadb.conf.d/50-server.cnf

COPY mariadb.sh /mariadb.sh

#RUN cp -rp /var/lib/mysql /var/lib/mysql_

#ENTRYPOINT /bin/bash -c 'source /mariadb.sh'



# ENTRYPOINT /bin/bash -c 'cd /var/lib/mysql_/ && \
# for f in $(ls) ; do \
#   if [[ ! -e /var/lib/mysql/${f} ]] ; \
#     then mv /var/lib/mysql_/${f} /var/lib/mysql/${f}; NEWSTART="TRUE" ; \
#   fi \
# done \
# && service mysql start \
# && sleep 2 \
# && if [[ "${NEWSTART}" == "TRUE"  ]] ; then source /mariadb.sh && sleep 5 && service mysql restart ; fi \
# && cd / && /bin/bash'

# docker build -t flaski/mariadb . 
# docker run -d \
# -v ~/flaski_data/mariadb:/var/lib/mysql
# -e myqsl_password=sqpass \
# -e MAINDB=flaski \
# -e PASSWDDB=flaskidbpass \
# --name mariadb -it flaski/mariadb

# docker run -v ~/flaski_data/mariadb:/var/lib/mysql -e myqsl_password=sqpass -e MAINDB=flaski -e PASSWDDB=flaskidbpass --name mariadb -it flaski/mariadb
# mysql -h 172.18.0.3 -u root -p
# SELECT host FROM mysql.user WHERE User = 'flaski';

#GRANT ALL ON *.* to flaski@'e18095a30855' IDENTIFIED BY 'flaski@e18095a30855';
#FLUSH PRIVILEGES;
#SELECT host FROM mysql.user WHERE User = 'root';