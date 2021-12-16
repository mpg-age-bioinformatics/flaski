# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.
ARG MYAPP_IMAGE=mpgagebioinformatics/myapp:latest
FROM $MYAPP_IMAGE

LABEL maintainer "bioinformatics@age.mpg.de"

ARG APP_VERSION
ENV APP_VERSION ${APP_VERSION}

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
COPY ./email/app_exception.html /myapp/myapp/templates/email/app_exception.html
COPY ./email/app_exception.txt /myapp/myapp/templates/email/app_exception.txt
COPY ./email/app_help.html /myapp/myapp/templates/email/app_help.html
COPY ./email/app_help.txt /myapp/myapp/templates/email/app_help.txt
USER myapp
