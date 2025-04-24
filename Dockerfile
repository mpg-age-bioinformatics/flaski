# Copyright (c) Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing.
# Distributed under the terms of the Modified BSD License.
ARG MYAPP_IMAGE=mpgagebioinformatics/myapp:latest
FROM $MYAPP_IMAGE

LABEL maintainer="bioinformatics@age.mpg.de"

ARG APP_VERSION
ENV APP_VERSION ${APP_VERSION}

ARG PYFLASKI_VERSION
ENV PYFLASKI_VERSION ${PYFLASKI_VERSION}

USER root

ENV DEB_PYTHON_INSTALL_LAYOUT=deb_system

# -o Acquire::Check-Valid-Until=false 
RUN apt-get update && apt-get install -yq libgirepository1.0-dev libcairo2-dev python3-dev pkg-config ninja-build build-essential gobject-introspection gcc libglib2.0-dev && \
apt-get clean && rm -rf /var/lib/apt/lists/*

COPY ./pyflaski/requirements.txt /pyflaski.requirements.txt
RUN pip3 install --no-cache-dir --prefer-binary -r /pyflaski.requirements.txt

COPY requirements.txt /requirements.txt
RUN pip3 install --no-cache-dir -r /requirements.txt

RUN mkdir -p /myapp/data/kegg /myapp/data/david /mpcdf /submissions_ftp /flaski_private /backup/oc_data /oc_data
RUN chown -R ${BUILD_NAME}:${BUILD_NAME} /submissions /flaski_private /mpcdf /backup/oc_data /oc_data /submissions_ftp


COPY ./static/dog-solid.png /myapp/myapp/static/favicon.ico
COPY ./static/dog-solid.png /myapp/myapp/static/logo.png
COPY ./pyflaski/pyflaski /myapp/pyflaski
COPY ./pyflaski/data/david /myapp/pyflaski/data/david
COPY ./pyflaski/data/kegg /myapp/pyflaski/data/kegg
COPY ./routes/home.py /myapp/myapp/routes/home.py
COPY ./routes/index.py /myapp/myapp/routes/index.py
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
COPY ./email/submissions.age.html /myapp/myapp/templates/email/submissions.age.html
COPY ./email/submissions.age.txt /myapp/myapp/templates/email/submissions.age.txt
COPY ./email/submissions.ftp.html /myapp/myapp/templates/email/submissions.ftp.html
COPY ./email/submissions.ftp.txt /myapp/myapp/templates/email/submissions.ftp.txt
COPY ./email/submissions.ftp.data.html /myapp/myapp/templates/email/submissions.ftp.data.html
COPY ./email/submissions.ftp.data.txt /myapp/myapp/templates/email/submissions.ftp.data.txt
COPY ./email/validate_email.html /myapp/myapp/templates/email/validate_email.html
COPY ./email/validate_email.txt /myapp/myapp/templates/email/validate_email.txt
COPY ./_models.py /myapp/myapp/_models.py

RUN chown -R ${BUILD_NAME}:${BUILD_NAME} /${BUILD_NAME}

USER myapp
