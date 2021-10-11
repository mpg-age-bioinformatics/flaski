# DEPLOYING

For additional info please check the `myapp` repository.

Clone flaski and the base myapp repo:

```
cd ~
git clone git@github.com:mpg-age-bioinformatics/myapp.git
git clone git@github.com:mpg-age-bioinformatics/flaski-3.0.0.git
```

If you need to generate self-signed certificates you can do so by:
```
mkdir -p ~/myapp_data/certificates 
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout ~/myapp_data/certificates/key.pem -out ~/myapp_data/certificates/cert.pem -subj "/C=DE/ST=NRW/L=Cologne/O=MPS/CN=myapp"
openssl dhparam -out ~/myapp_data/certificates/dhparam.pem 2048
```

On a Mac double click on the cert.pem file to open it and add it to the Keychain. In key chain double click on the certificate to change Trust : When using this certificate : Always trust.

Export secret variables:
```
cat << EOF > .env
MYSQL_PASSWORD=$(openssl rand -base64 20)
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 20)
REDIS_PASSWORD=$(openssl rand -base64 20)
SECRET_KEY=$(openssl rand -base64 20)
EOF
```

Create local folders:
```
mkdir -p ~/flaski3_backup/stats ~/flaski3_backup/users_data ~/flaski3_backup/mariadb
```

To deploy flaski edit the docker-compose.yml accordingly and then:
```
docker-compose up -d --build
```

If running myapp on development mode you will have to start flask from inside the server container:
```
docker-compose exec server /bin/bash
flask run --host 0.0.0.0 --port 8000
```
Adding administrator user:
```
docker-compose run --entrypoint="python3 /myapp/myapp.py admin --add myemail@gmail.com" init
```

### Email logging

To use the SMTP debugging server from Python comment all email related `env` in `docker-compose.yml`.
You can not using python's fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```bash
docker-compose exec server python3 -m smtpd -n -c DebuggingServer localhost:8025
```

### pyflaski

pyflaski was added as a submodule of flaski:
```
cd flaski-3.0.0
git submodule add git@github.com:mpg-age-bioinformatics/pyflaski.git pyflaski
git submodule init pyflaski
```
To update from the remote:
```
git submodule update pyflaski
```
Commiting changes:
```
cd ~/flaski-3.0.0/pyflaski
git add -A . 
git commit -m "<describe your changes here>"
git push origin HEAD:master
```
then tell the main project to start tracking the updated version:
```
cd ~/flaski-3.0.0
git add pyflaski
git commit -m pyflaski
git push
```