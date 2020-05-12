#!/bin/bash

git add -A . 
git commit -m "$1"
docker build -t flaski/flaski:dev . && docker push flaski/flaski:dev