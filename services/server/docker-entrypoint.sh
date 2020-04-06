#!/bin/bash

if [[ "$FLASK_ENV" == "init" ]] ; then

  while ! mysqladmin --user=root --password=${MYSQL_ROOT_PASSWORD} --host=${MYSQL_HOST} status ; 
    do echo "Waiting for mysql.. " && sleep 4
  done

  if mysql --user=${MYSQL_USER} --password="${MYSQL_PASSWORD}" --host=${MYSQL_HOST} -e "use flaski";
    then
      echo "Flaski database already exists."
    else

mysql --user=root --password=${MYSQL_ROOT_PASSWORD} --host=${MYSQL_HOST} << _EOF_
CREATE USER '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE USER '${MYSQL_USER}'@'%' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE DATABASE flaski /*\!40100 DEFAULT CHARACTER SET utf8 */;
GRANT ALL PRIVILEGES ON flaski.* TO 'root'@'%';
GRANT ALL PRIVILEGES ON flaski.* TO '${MYSQL_USER}'@'%';
FLUSH PRIVILEGES;
_EOF_

      echo "mysql database created.."
  fi

  if [[ "$RESTORE_DB" == "1" ]] ; then
    touch /mysql_backup.log
    touch /rsync.log
    tail -F /mysql_backup.log /rsync.log &
    echo "=> Restore latest backup"
    LATEST_BACKUP=$(find /backup/mariadb -maxdepth 1 -name '*.sql.gz' | tail -1 )
    echo "=> Restore database from ${LATEST_BACKUP}"
    set -o pipefail
    if gunzip --stdout "${LATEST_BACKUP}" | mysql -h "${MYSQL_HOST}" -u "${MYSQL_USER}" -p"${MYSQL_PASSWORD}"
      then
        echo "=> Restore succeeded"
      else
        echo "=> Restore failed"
    fi
  fi

  mysql --user=${MYSQL_USER} --password="${MYSQL_PASSWORD}" --host=${MYSQL_HOST} << _EOF_
USE flaski
DROP TABLE IF EXISTS alembic_version;
_EOF_

  rm -rf migrations/* 
  flask db init && flask db migrate -m "users table" && flask db upgrade && flask db migrate -m "userloggings table" && flask db upgrade

  exit

else

  while ! mysql --user=${MYSQL_USER} --password="${MYSQL_PASSWORD}" --host=${MYSQL_HOST} -e "use flaski"; 
    do echo "Waiting for mysql.. " && sleep 4
  done
  echo "Found flaski db."


  if [[ "$FLASK_ENV" == "production" ]] ; then
    gunicorn -b 0.0.0.0:8000 -w 4 flaski:app
  elif [[ "$FLASK_ENV" == "development" ]] ; then
    tail -f /dev/null
  fi

fi

# ## needs to be finished, this is for the managment containter
# if [[ "$FLASK_ENV" == "mngt" ]]

#   echo "0 0 1,15 * * python3 /flaski/flaski.py > /clean.flaski.out 2>&1" > /cron.job && crontab /cron.job

# fi

