#!/bin/bash

# usage:
#
# deploy 
# $ deploy.sh
#
# deploy after docker-compose down
# $ deploy.sh down
#
# deploy at 4 am
# $ deploy.sh up 04:00 &
#
# deploy at 4 am after doing a docker-compose down
# $ deploy.sh down 04:00 &

set -o errexit

readonly LOG_FILE="/srv/logs/deploy.$(date '+%Y%m%d.%H%M%S').out"

# Create the destination log file that we can
# inspect later if something goes wrong with the
# initialization.
touch $LOG_FILE

# get the LOG_FILE in your stdout
tail -f $LOG_FILE &

# Open standard out at `$LOG_FILE` for write.
# This has the effect 
exec 1>$LOG_FILE

# Redirect standard error to standard out such that 
# standard error ends up going to wherever standard
# out goes (the file).
exec 2>&1

cd /srv/flaski

if [ -z "$2" ] ; 
then
    echo "$(date) :: Depolying now!"
else
    echo "$(date) :: Deploying at ${2}"
    until [[ "$(date +%H:%M)" == "${2}" ]]; do
        sleep 25
    done
    echo "$(date) :: Depolying now!"
fi

BASE_IMAGES="flaski/flaski:latest" 
#  flaski/backup:latest redis:5 nginx:alpine mariadb:10.4"

DEPLOY="0"

for BASE_IMAGE in ${BASE_IMAGES}; do

    #REGISTRY="registry.hub.docker.com"
    #IMAGE="$REGISTRY/$BASE_IMAGE"
    IMAGE=$BASE_IMAGE
    CID=$(docker ps | grep $IMAGE | awk '{print $1}')
    echo "$(date) :: docker pull $IMAGE started\n####################################"
    docker pull $IMAGE
    echo "####################################\n$(date) :: docker pull $IMAGE finished\n"

    for im in $CID
    do
        LATEST=`docker inspect --format "{{.Id}}" $IMAGE`
        RUNNING=`docker inspect --format "{{.Image}}" $im`
        NAME=`docker inspect --format '{{.Name}}' $im | sed "s/\///g"`
        echo "$(date) :: Latest:" $LATEST
        echo "$(date) :: Running:" $RUNNING
        if [ "$RUNNING" != "$LATEST" ];then
            echo "$(date) :: $NAME needs upgrading"
            DEPLOY="1"
        else
            echo "$(date) :: $NAME up to date"
        fi
    done
done

if [[ "$DEPLOY" == "1" ]] ; then

    if [[ "$1" == "down" ]] ; 
        then

            docker-compose -f production.yml pull server && \
            docker-compose -f production.yml exec backup /backup.sh && \
            docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
            echo "$(date) :: docker-compose down" && \
            docker-compose -f production.yml down && \
            echo "$(date) :: docker-compose up -d" && \
            docker-compose -f production.yml up -d

        else

            docker-compose -f production.yml pull server && \
            docker-compose -f production.yml exec backup /backup.sh && \
            docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
            echo "$(date) :: docker-compose up -d" && \
            docker-compose -f production.yml up -d server

    fi
fi

echo "$(date) :: Done!"

