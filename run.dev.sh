#!/bin/bash

mkdir -p ~/flaski_data/data ~/flaski_data/redis ~/flaski_data/users ~/flaski_data/logs
docker stop flaski
docker rm flaski
docker run -p 5000:5000 -p 8888:8888 \
-e FLASK_ENV=development \
-v ~/flask_dashboard:/flaski -v ~/flaski_data:/flaski_data \
--name flaski -it flaski