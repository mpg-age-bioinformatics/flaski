#!/bin/bash

git add -A . 
git commit -m "$1"
docker build -t flaski/flaski:dev . && docker push flaski/flaski:dev && sleep 5 && curl -X POST https://portainer.age.mpg.de/api/webhooks/304d48ea-8495-497e-933d-49c8be2f2ef7