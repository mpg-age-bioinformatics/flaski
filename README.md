# Flaski

## Build docker image and generate certificates

```
docker build -t flaski .
mkdir -p ~/flaski_data/data ~/flaski_data/redis ~/flaski_data/users ~/flaski_data/logs ~/flaski_data/certificates
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout ~/flaski_data/certificates/key.pem -out ~/flaski_data/certificates/cert.pem -subj "/C=DE/ST=NRW/L=Cologne/O=MPS/CN=flaski"
```

## Development
```
docker run -p 5000:5000 -e FLASK_ENV=development -v ~/flaski:/flaski -v ~/flaski_data:/flaski_data --name flaski -it flaski
```

## Production

Make sure the `my_redis_password` in `requirepass my_redis_password` of the `redis.conf` line 507 matches the `my_redis_password` you will be issuing with `-e`.

```
docker run -p 5000:5000 -p 443:443 -p 8888:8888 -p 8041:8041 -p 8080:8080
-v ~/flaski_data:/flaski_data -v ~/flaski:/flaski
-e REDIS_PASSWORD=my_redis_password 
-e SESSION_TYPE=redis 
-e REDIS_ADDRESS='127.0.0.1:6379/0'
-e DATABASE_URL='mysql+pymysql://flaski:flaskidbpass@localhost:3306/flaski'
-e MAIL_SERVER='mail.age.mpg.de'
-e MAIL_PORT=25
-e MAIL_USE_TLS=1
-e MAIL_USERNAME='flaski@age.mpg.de'
-e MAIL_PASSWORD='my_flaski_email_password'
--name flaski -it flaski
```

or, during testing:

```
docker run -p 80:80 -p 443:443 -v ~/flaski:/flaski -v ~/flaski_data:/flaski_data --name flaski -it flaski
```

## Databases

Starting
```
rm -rf migrations && flask db init && flask db migrate -m "users table" && flask db upgrade 
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
