#!/bin/bash

cd /srv/flaski

if [[ "$1" == "down" ]] ; 
    then


        docker-compose -f production.yml exec backup /backup.sh && \
        docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
        docker-compose -f production.yml pull && \
        docker-compose -f production.yml down && \
        docker-compose -f production.yml up -d

    else

        docker-compose -f production.yml exec backup /backup.sh && \
        docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
        docker-compose -f production.yml pull && \
        docker-compose -f production.yml up -d

fi
