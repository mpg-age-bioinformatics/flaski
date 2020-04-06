FROM jwilder/dockerize

LABEL maintainer "Daniel Rosskopp <drosskopp@upcal.de>"

RUN apk add --update bash mysql-client gzip openssl rsync && rm -rf /var/cache/apk/*

ENV CRON_TIME="0 3 * * *" \
    MYSQL_HOST="mariadb" \
    MYSQL_PORT="3306" \
    TIMEOUT="30s"

COPY ["run.sh", "backup.sh", "restore.sh", "/"]
RUN mkdir -p /backup/users_data /backup/mariadb /flaski_data && chmod u+x /backup.sh /restore.sh /run.sh
VOLUME ["/backup"]

CMD dockerize -wait tcp://${MYSQL_HOST}:${MYSQL_PORT} -timeout ${TIMEOUT} /run.sh