# Flaski

Flaski is a flask based collection of web apps for life-sciences. Flaski can be deployed using the docker-compose.yml or on a kubernetes cluster. Within Flaski, pyflaski provides access to all the main functions used by the different web applications.

## Deploying Flaski

If you need to generate self-signed certificates you can do so by:
```
mkdir ~/flaski_data/certificates
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout ~/flaski_data/certificates/key.pem -out ~/flaski_data/certificates/cert.pem -subj "/C=DE/ST=NRW/L=Cologne/O=MPS/CN=flaski"
```
If running flaski on development mode make sure that you change the variable `FLASK_ENV` to `development` in `docker-compose.yml`.

Export secret variables:
```bash
export MAIL_PASSWORD="<mail password>"
export MYSQL_ROOT_PASSWORD=$(openssl rand -base64 20)
export REDIS_PASSWORD=$(openssl rand -base64 20)
export SECRET_KEY=$(openssl rand -base64 20)
```

To deploy Flaski edit the `docker-compose.yml` accordingly and then:
```bash
docker-compose up -d --build
```
Check the `stdout` with:
```bash
docker-compose logs
```
or for example:
```bash
docker-compose logs -f server
```
You can connect to any of the running containers by eg. 
```bash
docker-compose exec mariadb /bin/bash
```
For stopping and removing a container,
```bash
docker-compose stop mariadb && docker-compose rm mariadb
```
Stopping and removing all containers:
```bash
docker-compose down
```
Stopping and removing all containers as well as all volumes (this will destroy the volumes and contained data):
```bash
docker-compose down -v
```
To remove a volume, eg.
```bash
docker volume rm db
```

## Backup of mysql and user files to host

```bash
mkdir ~/flaski_backups
docker run -it -v flaski_backups:/backups -v ~/flaski_backups:/host mariadb/server rsync -rtvh --delete /backups/ /host
```

optionally remove mysql backups from volume:
```bash
docker run -it -v flaski_backups:/backups -v ~/flaski_backups:/host mariadb/server rm -rf /backups/mariadb/*
```

## Email logging

To use the SMTP debugging server from Python comment all email related `env` in `docker-compose.yml`.
You can not using python's fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```bash
docker-compose exec server python3 -m smtpd -n -c DebuggingServer localhost:8025
```

## Databases

For handling database entries you can start the `flask shell` by:
```bash
docker-compose exec server flask shell 
```
and then for removing a user from the db:
```python
u=User.query.filter_by(email=<user_email>).first()
db.session.delete(u)
```
for editing entries eg.:
```python
user=User.query.filter_by(email=<user_email>).first()
user.active = False
db.session.add(user)
db.session.commit()
```

If you need to re-iniate your database
```bash
rm -rf migrations && flask db init && flask db migrate -m "users table" && flask db upgrade 
```

upgrading
```bash
flask db migrate -m "new fields in user model"
flask db upgrade
```

Backup a database:
```bash
docker-compose exec mariadb /usr/bin/mysqldump -u root --password=mypass flaski > dump.sql
```

Restore a database from backup:
```bash
cat dump.sql | docker-compose exec mariadb mysql --user=root --password=mypass flaski
```

*Backup with `mariabackup`*

1st backup:
```bash
mariabackup --backup \
   --target-dir=/var/mariadb/backup/ \
   --user=root --password=mypass
```

2nd backup:
```bash
mariabackup --backup \
   --incremental-basedir=/var/mariadb/backup/
   --target-dir=/var/mariadb/inc1/ \
   --user=root --password=mypass
```

3rd backup:
```bash
mariabackup --backup \
   --target-dir=/var/mariadb/inc2/ \
   --incremental-basedir=/var/mariadb/inc1/ \
   --user=root --password=mypass
```

*Restore from incremental backups with `mariabackup`*
```bash
mariabackup --prepare \
   --target-dir=/var/mariadb/backup
mariabackup --prepare \
   --target-dir=/var/mariadb/backup \
   --incremental-dir=/var/mariadb/inc1
.
.
.
mariabackup --prepare \
   --target-dir=/var/mariadb/backup \
   --incremental-dir=/var/mariadb/incN

mariabackup --copy-back \
   --target-dir=/var/mariadb/backup/

chown -R mysql:mysql /var/lib/mysql/
```

## Build and Install

```bash
python3 setup.py bdist_wheel
pip3 install flaski-0.1.0-py3-none-any.whl
```
Static files need to be included in the `MANIFEST.in`.

