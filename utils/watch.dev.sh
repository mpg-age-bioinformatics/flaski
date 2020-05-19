#!/bin/bash

cd /srv/flaski

while docker-compose -f production.yml up -d server
do
    sleep 30
done
