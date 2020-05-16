#!/usr/bin/env bash
set -e
BASE_IMAGES="flaski/flaski:latest"#  flaski/backup:latest redis:5 nginx:alpine mariadb:10.4"

DEPLOY="0"

for BASE_IMAGE in ${BASE_IMAGES}; do

    #REGISTRY="registry.hub.docker.com"
    #IMAGE="$REGISTRY/$BASE_IMAGE"
    IMAGE=$BASE_IMAGE
    CID=$(docker ps | grep $IMAGE | awk '{print $1}')
    docker pull $IMAGE

    for im in $CID
    do
        LATEST=`docker inspect --format "{{.Id}}" $IMAGE`
        RUNNING=`docker inspect --format "{{.Image}}" $im`
        NAME=`docker inspect --format '{{.Name}}' $im | sed "s/\///g"`
        echo "Latest:" $LATEST
        echo "Running:" $RUNNING
        if [ "$RUNNING" != "$LATEST" ];then
            echo "$NAME needs upgrading"
            DEPLOY="1"
            #stop docker-$NAME
            #docker rm -f $NAME
            #start docker-$NAME
        else
            echo "$NAME up to date"
        fi
    done
done

if [[ "$DEPLOY" == "1" ]] ; then

/srv/flaski/utils/deploy.sh

fi