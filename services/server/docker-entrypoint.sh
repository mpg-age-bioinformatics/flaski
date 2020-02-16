#!/bin/bash


while ! mysqladmin --user=${MYSQL_USER} --password=${MYSQL_ROOT_PASSWORD} --host=${MYSQL_HOST} status ; 
  do echo "Waiting for mysql.. " && sleep 4
done

if mysql --user=${MYSQL_USER} --password=${MYSQL_ROOT_PASSWORD} --host=${MYSQL_HOST} -e "use flaski";
  then
    echo "Flaski database already exists."
  else
mysql --user=${MYSQL_USER} --password=${MYSQL_ROOT_PASSWORD} --host=${MYSQL_HOST} << _EOF_
CREATE DATABASE flaski /*\!40100 DEFAULT CHARACTER SET utf8 */;
GRANT ALL PRIVILEGES ON flaski.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
_EOF_

echo "mysql database created"

rm -rf migrations 
flask db init && flask db migrate -m "users table" && flask db upgrade && flask db migrate -m "userloggings table" 
fi

if [[ "$FLASK_ENV" == "development" ]] ; then
  flask run --host 0.0.0.0 --port 8000 # python3 -m smtpd -n -c DebuggingServer localhost:8025
else
  gunicorn -b 0.0.0.0:8000 -w 4 flaski:app
fi