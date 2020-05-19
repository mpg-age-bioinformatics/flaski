#!/bin/bash

cd /srv/flaski

while true
do

    BASE_IMAGES=$(docker ps | grep server | awk '{ print $2 }') 
    #  flaski/backup:latest redis:5 nginx:alpine mariadb:10.4"

    DEPLOY="0"

    for BASE_IMAGE in ${BASE_IMAGES}; do

        #REGISTRY="registry.hub.docker.com"
        #IMAGE="$REGISTRY/$BASE_IMAGE"
        IMAGE=$BASE_IMAGE
        CID=$(docker ps | grep $IMAGE | awk '{print $1}')
        echo "$(date) :: docker pull $IMAGE started"
        echo "####################################"
        docker pull $IMAGE
        echo "####################################"
        echo "$(date) :: docker pull $IMAGE finished"

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

        docker-compose -f production.yml pull server && \
        docker-compose -f production.yml exec backup /backup.sh && \
        docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
        echo "$(date) :: docker-compose up -d" && \
        docker-compose -f production.yml up -d server

    fi

    echo "$(date) :: Done!"

    sleep 30

done
