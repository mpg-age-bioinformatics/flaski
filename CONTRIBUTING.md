# CONTRIBUTING

For additional info please check the `myapp` repository.

Clone flaski and the base myapp repo:

```
cd ~
git clone git@github.com:mpg-age-bioinformatics/myapp.git
git clone git@github.com:mpg-age-bioinformatics/flaski.git
```

Export secret variables:
```
cd ~/flaski
cat << EOF > .env
MYSQL_PASSWORD=$(openssl rand -base64 20 | tr -d '/')
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 20 | tr -d '/')
REDIS_PASSWORD=$(openssl rand -base64 20 | tr -d '/')
SECRET_KEY=$(openssl rand -base64 20 | tr -d '/')
EOF
```

Create local folders:
```
mkdir -p ~/flaski23/backup/stats ~/flaski23/backup/users_data2 ~/flaski23/backup/users_data3 ~/flaski23/backup/mariadb ~/flaski23/private ~/flaski23/mpcdf ~/flaski23/submissions
```

To deploy flaski edit the docker-compose.yml accordingly and then pull pyflaski and build:
```
cd ~/flaski
git submodule update --init --recursive
docker-compose up -d --build
```

If running myapp on development mode you will have to start flask from inside the server container:
```
docker-compose exec server3 /bin/bash
flask run --host 0.0.0.0 --port 8000
```
Add the following line to your `/etc/hosts`
```
127.0.0.1       flaski.localhost
```

You can now access flaski over https://flaski.localhost/v3.

Adding administrator user:
```
docker-compose run --entrypoint="python3 /myapp/myapp.py admin --add myemail@gmail.com" init
```

### Email logging

To use the SMTP debugging server from Python comment all email related `env` in `docker-compose.yml`.
You can not using python's fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```bash
docker-compose exec server3 python3 -m smtpd -n -c DebuggingServer localhost:8025
```

### pyflaski

pyflaski was added as a submodule of flaski:
```
cd ~/flaski
git submodule add git@github.com:mpg-age-bioinformatics/pyflaski.git pyflaski
git submodule init pyflaski
```

If making a fresh clone you will need to:
```
cd ~/flaski
git submodule update --init --recursive
```

To update from the remote:
```
git submodule update --recursive --remote
```

Commiting changes:
```
cd ~/flaski/pyflaski
git add -A . 
git commit -m "<describe your changes here>"
git push origin HEAD:master
```

then tell the main project to start tracking the updated version:
```
cd ~/flaski
git add pyflaski
git commit -m pyflaski
git push
```
