# Flaski

## Development

If running flaski on development mode make sure you generate self signed certificates first:
```
mkdir ~/flaski_data/certificates
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout ~/flaski_data/certificates/key.pem -out ~/flaski_data/certificates/cert.pem -subj "/C=DE/ST=NRW/L=Cologne/O=MPS/CN=flaski"
```
and that you change the variable `FLASK_ENV` to `development`.

## Deploying Flaski

Edit the `docker-compose.yml` accordingly and then:
```
docker-compose up -d --build
```
You can connect to any of the running containers by eg. 
```
docker-compose exec mariadb /bin/bash
```
For stopping and removing a container,
```
docker-compose stop mariadb && docker-compose rm mariadb
```
To remove a volume, eg.
```
docker volume rm db
```

## Email logging

To use the SMTP debugging server from Python. 
This is a fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```
docker-compose exec server python3 -m smtpd -n -c DebuggingServer localhost:8025
```

## Databases

If you need to re-iniate your database
```
rm -rf migrations && flask db init && flask db migrate -m "users table" && flask db upgrade 
```

upgrading

```
flask db migrate -m "new fields in user model"
flask db upgrade
```

## Build and Install

```
python3 setup.py bdist_wheel
pip3 install flaski-0.1.0-py3-none-any.whl
```

Static files need to be included in the `MANIFEST.in`.