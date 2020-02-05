# Flaski

## Deploying Flaski

If you need to generate self-signed certificates you can do so by:
```
mkdir ~/flaski_data/certificates
openssl req -new -newkey rsa:4096 -days 365 -nodes -x509 -keyout ~/flaski_data/certificates/key.pem -out ~/flaski_data/certificates/cert.pem -subj "/C=DE/ST=NRW/L=Cologne/O=MPS/CN=flaski"
```
If running flaski on development mode make sure that you change the variable `FLASK_ENV` to `development`.

To deploy Flaski edit the `docker-compose.yml` accordingly and then:
```
docker-compose up -d --build
```
Check the `stdout` with:
```
docker-compose logs
```
or for example:
```
docker-compose logs -f server
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
Backup a database:
docker-compose exec mariadb /usr/bin/mysqldump -u root --password=mypass flaski > dump.sql

Restore a database from backup:
```
cat dump.sql | docker-compose exec mariadb mysql --user=root --password=mypass flaski
```

*Backup with `mariabackup`*

1st backup:
```
mariabackup --backup \
   --target-dir=/var/mariadb/backup/ \
   --user=root --password=mypass
```

2nd backup:
```
mariabackup --backup \
   --incremental-basedir=/var/mariadb/backup/
   --target-dir=/var/mariadb/inc1/ \
   --user=root --password=mypass
```

3rd backup:
```
mariabackup --backup \
   --target-dir=/var/mariadb/inc2/ \
   --incremental-basedir=/var/mariadb/inc1/ \
   --user=root --password=mypass
```

*Restore from incremental backups with `mariabackup`*
```
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

```
python3 setup.py bdist_wheel
pip3 install flaski-0.1.0-py3-none-any.whl
```
Static files need to be included in the `MANIFEST.in`.