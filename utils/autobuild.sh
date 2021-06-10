#!/bin/bash

if [[ ! -z $(git status -uno --porcelain) ]] ;
then
    echo $(date +"%Y/%m/%d %H:%M:%S")": all changes have been commited"
else
    echo ""
    echo ""
    echo $(date +"%Y/%m/%d %H:%M:%S")": PLEASE COMMIT YOUR CHANGE FIRST!!!"
    echo ""
    echo ""
    git status
fi

while [[ $# -gt 0 ]]
do
  case $1 in
    -h|--help)
      echo "$USAGE"
      exit
      ;;
    -f|--force)
      FORCE=true
      shift
      ;;
    -p|--production)
      PRODUCTION=true
      shift
      ;;
    *)
      echo "error: unsupported option '$1'. See '$(basename $0) --help'."
      exit 65
      ;;
  esac
  shift
done

# readlink -f does not work on mac
current=$(dirname ${0})
cd ${current}
current=$(pwd)

cd ../

if [ "${FORCE}" = true ] ; then
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest commit"
    git pull
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest tag"
    git fetch --tags --all
    local_tag=$(git tag -l --sort=refname | tail -n 1 )
    echo $(date +"%Y/%m/%d %H:%M:%S")": building image"
    docker-compose build server
    docker tag flaski_server:latest flaski/flaski:dev
    if [ "${PRODUCTION}" = true ] ; then
        git checkout ${local_tag}
        docker-compose build server
        docker tag flaski_server:latest flaski/flaski:latest
        docker tag flaski_server:latest flaski/flaski:${local_tag}
        git checkout master
    fi
    echo $(date +"%Y/%m/%d %H:%M:%S")": pushing image"
    docker push flaski/flaski:dev
    if [ "${PRODUCTION}" = true ] ; then
        docker push flaski/flaski:latest
        docker push flaski/flaski:${local_tag}
    fi
exit
fi

# get local sha and tag
local_tag=$(git tag -l --sort=refname | tail -n 1 )
local_sha=$(git rev-parse master)

# remote sha and tag
remote_tag=$(git ls-remote --tags https://github.com/mpg-age-bioinformatics/flaski.git | cut -f 2 | tail -n 2 | head -n 1 | awk -F/ '{ print $3 }')
remote_sha=$(git ls-remote https://github.com/mpg-age-bioinformatics/flaski.git | cut -f 1 | head -n 1)

# do one first check and pull of git to avoid the next cron job overwriting this one
if [[ "${local_sha}" != "${remote_sha}" ]] ; then 
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest commit"
    git pull
else
    echo $(date +"%Y/%m/%d %H:%M:%S")": no new commits"
fi

if [[ "${local_tag}" != "${remote_tag}" ]] ; then 
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest tag"
    git pull
    git fetch --tags --all
else
    echo $(date +"%Y/%m/%d %H:%M:%S")": no new tags"
fi

# now repeat but this time building the images
if [[ "${local_sha}" != "${remote_sha}" ]] ; then 
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest commit"
    git pull
    echo $(date +"%Y/%m/%d %H:%M:%S")": building image"
    docker-compose build server
    docker tag flaski_server:latest flaski/flaski:dev
    echo $(date +"%Y/%m/%d %H:%M:%S")": pushing image"
    docker push flaski/flaski:dev
fi

if [[ "${local_tag}" != "${remote_tag}" ]] ; then 
    echo $(date +"%Y/%m/%d %H:%M:%S")": pulling latest tag"
    git pull
    git fetch --tags --all
    git checkout ${remote_tag}
    echo $(date +"%Y/%m/%d %H:%M:%S")": building image"
    docker-compose build server
    docker tag flaski_server:latest flaski/flaski:latest
    docker tag flaski_server:latest flaski/flaski:${remote_tag}
    git checkout master
    echo $(date +"%Y/%m/%d %H:%M:%S")": pushing image"
    docker push flaski/flaski:latest
    docker push flaski/flaski:${remote_tag}
fi