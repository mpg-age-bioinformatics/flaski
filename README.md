# Flaski

## Development

### Build the docker image and run the container

```
docker build -t flaski .
mkdir -p ~/flaski_data/data ~/flaski_data/redis ~/flaski_data/users ~/flaski_data/logs
docker run -p 5000:5000 -p 8888:8888 -e FLASK_ENV=development -v ~/flask_dashboard:/flaski -v ~/flaski_data:/flaski_data --name flaski -it flaski
```

### Start flask, redis, and python email dev logger

```
python3 -m smtpd -n -c DebuggingServer localhost:8025 & redis-server redis.conf --daemonize yes && flask run --host 0.0.0.0
```

### or ..

```
utils/run.dev.sh
```

# Production

### Run the docker image

Make sure the `my_redis_password` in `requirepass my_redis_password` of the `redis.conf` line 507 matches the `my_redis_password` you will be issuing with `-e`.

```
docker run -p 5000:5000 -p 8888:8888 
-v ~/flask_dashboard:/flaski -v ~/flaski_data:/data -v ~/flaski_redis:/redis 
-e REDIS_PASSWORD=my_redis_password 
-e SESSION_TYPE=redis 
-e REDIS_ADDRESS='127.0.0.1:6379/0'
-e DATABASE_URL='sqlite:///data/app.db'
-e MAIL_SERVER='mail.age.mpg.de'
-e MAIL_PORT=25
-e MAIL_USE_TLS=1
-e MAIL_USERNAME='flaski@age.mpg.de'
-e MAIL_PASSWORD='my_flaski_email_password'
--name flaski -it flaski /bin/bash
```

### Start flask, redis

```
redis-server redis.conf --daemonize yes && flask run --host 0.0.0.0
```

## Databases

Starting
```
rm -rf app.db migrations /flaski_data/data/*
flask db init
flask db migrate -m "users table"
flask db upgrade 
```

upgrading
```
flask db migrate -m "new fields in user model"
flask db upgrade
```

## Logging

There are two approaches to test email logging. The easiest one is to use the SMTP debugging server from Python. 
This is a fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```
python3 -m smtpd -n -c DebuggingServer localhost:8025 & 
```
and 
```
export MAIL_SERVER=localhost
export MAIL_PORT=8025
```
before running your app.

A second testing approach for this feature is to configure a real email server. 
Below is the configuration to use your Gmail account's email server:
```
export MAIL_SERVER=smtp.googlemail.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USERNAME=<your-gmail-username>
export MAIL_PASSWORD=<your-gmail-password>
```

## Build and Install

https://flask.palletsprojects.com/en/1.1.x/tutorial/deploy/

Static files need to be included in the `MANIFEST.in`.

```
python3 setup.py bdist_wheel
pip3 install flaski-0.1.0-py3-none-any.whl
```
