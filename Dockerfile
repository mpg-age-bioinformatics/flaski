# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.

# Debian buster-slim (10.1)
FROM flaski/debian

LABEL maintainer "bioinformatics@age.mpg.de"

RUN apt-get update && apt-get -yq dist-upgrade && \
apt-get install -yq python3 python3-pip libcairo2-dev pkg-config python3-dev mariadb-client && \
apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip3 install pymysql

# data folders
RUN mkdir -p /flaski/flaski /faski_data/users /faski_data/logs

COPY flaski .flaskenv config.py flaski.py LICENSE.md MANIFEST.in README.md requirements.txt setup.py pyflaski /flaski/

RUN pip3 install -r /flaski/requirements.txt

# Jupyter port
EXPOSE 8888
# Flask
EXPOSE 8000

WORKDIR /flaski

ENTRYPOINT /bin/bash -c 'flask db init && \
flask db migrate -m "users table" && \
flask db upgrade && \
if [[ "$FLASK_ENV" == "development" ]] ; \
  then \
    python3 -m smtpd -n -c DebuggingServer localhost:8025 & flask run --host 0.0.0.0 --port 8000 ; \
  else \
    gunicorn -b localhost:8000 -w 4 flaski:app ; \
fi ; \
/bin/bash'

# docker build -t flaski/app .
#docker run -d 
#-v ~/flaski_data:/flaski_data -v ~/flaski:/flaski
#-e REDIS_PASSWORD=my_redis_password 
#-e SESSION_TYPE=redis 
#-e REDIS_ADDRESS='127.0.0.1:6379/0'
#-e DATABASE_URL='mysql+pymysql://flaski:flaskidbpass@localhost:3306/flaski'
#--name flaski -it flaski
