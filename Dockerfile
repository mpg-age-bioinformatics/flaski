# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.
FROM mpgagebioinformatics/myapp:stable

LABEL maintainer "bioinformatics@age.mpg.de"

ARG MYAPP_VERSION
ENV MYAPP_VERSION ${MYAPP_VERSION}

USER root

COPY ./pyflaski/requirements.txt /pyflaski.requirements.txt
RUN pip3 install -r /pyflaski.requirements.txt

COPY ./static/dog-solid.png /myapp/myapp/static/favicon.ico
COPY ./static/dog-solid.png /myapp/myapp/static/logo.png
COPY ./pyflaski/pyflaski /myapp/pyflaski
COPY ./routes/apps /myapp/myapp/routes/apps
COPY ./routes/_routes.py /myapp/myapp/routes/_routes.py
COPY ./routes/_impressum.py /myapp/myapp/routes/_impressum.py
COPY ./routes/_vars.py /myapp/myapp/routes/_vars.py
COPY ./routes/_privacy.py /myapp/myapp/routes/_privacy.py
COPY ./routes/_about.py /myapp/myapp/routes/_about.py

USER myapp
