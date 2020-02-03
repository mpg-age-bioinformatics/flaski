#!/bin/bash


while ! mysqladmin --user=root --password=${MYSQL_ROOT_PASSWORD} --host=mariadb status ; 
  do echo "Waiting for mysql.. " && sleep 4
done

if mysql --user=root --password=${MYSQL_ROOT_PASSWORD} --host=mariadb -e "use flaski";
  then
    echo "Flaski database already exists."
  else
mysql --user=root --password=${MYSQL_ROOT_PASSWORD} --host=mariadb << _EOF_
CREATE DATABASE flaski /*\!40100 DEFAULT CHARACTER SET utf8 */;
GRANT ALL PRIVILEGES ON flaski.* TO 'root'@'%';
FLUSH PRIVILEGES;
_EOF_

echo "mysql database created"

rm -rf migrations 
flask db init && flask db migrate -m "users table" && flask db upgrade

fi

if [[ "$FLASK_ENV" == "development" ]] ; then
  flask run --host 0.0.0.0 --port 8000 # python3 -m smtpd -n -c DebuggingServer localhost:8025
else
  gunicorn -b 0.0.0.0:8000 -w 4 flaski:app
fi