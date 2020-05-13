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


if [[ "$1" == "down" ]] ; 
    then

        docker-compose -f production.yml exec backup /backup.sh >  && \
        docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
        docker-compose -f production.yml pull server && \
        echo "$(date) :: docker-compose down" && \
        docker-compose -f production.yml down && \
        echo "$(date) :: docker-compose up -d" && \
        docker-compose -f production.yml up -d

    else

        docker-compose -f production.yml exec backup /backup.sh && \
        docker-compose -f production.yml exec backup rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ && \
        docker-compose -f production.yml pull server && \
        echo "$(date) :: docker-compose up -d" && \
        docker-compose -f production.yml up -d server

fi

echo "$(date) :: Done!"

