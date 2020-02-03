mysql -e "CREATE DATABASE ${MAINDB} /*\!40100 DEFAULT CHARACTER SET utf8 */;"
mysql -e "GRANT ALL PRIVILEGES ON ${MAINDB}.* TO 'root'@'%';"
mysql -e "FLUSH PRIVILEGES;"


CREATE DATABASE IF NOT EXISTS ${MAINDB} CHARACTER SET utf8 */;


if mysql --user=root --password=mypass --host=mariadb -e "use flaski";
then
echo "Database flaski already exists. Exiting."
exit
else
echo Create database
fi