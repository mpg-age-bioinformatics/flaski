#!/bin/bash
touch /mysql_backup.log
touch /rsync.log
tail -F /mysql_backup.log /rsync.log &

if [ "${INIT_BACKUP}" -gt "0" ]; then
  echo "=> Create a backup on the startup"
  /backup.sh
elif [ -n "${INIT_RESTORE_LATEST}" ]; then
  echo "=> Restore latest backup"
  until nc -z "$MYSQL_HOST" "$MYSQL_PORT"
  do
      echo "waiting database container..."
      sleep 1
  done
find /backup/mariadb -maxdepth 1 -name 'latest.flaski.sql.gz' | tail -1 | xargs /restore.sh
fi

echo "${CRON_TIME} /backup.sh >> /mysql_backup.log 2>&1" > /crontab.conf
echo "${CRON_TIME} rsync -rtvh --delete /flaski_data/users/ /backup/users_data/ >> /rsync.log 2>&1" >> /crontab.conf
crontab /crontab.conf
echo "=> Running cron task manager"
exec crond -f
