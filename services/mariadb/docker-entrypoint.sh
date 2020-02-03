#!/bin/bash
set -eo pipefail
shopt -s nullglob

# if command starts with an option, prepend mysqld
if [ "${1:0:1}" = '-' ]; then
	set -- mysqld "$@"
fi

# skip setup if they want an option that stops mysqld
wantHelp=
for arg; do
	case "$arg" in
		-'?'|--help|--print-defaults|-V|--version)
			wantHelp=1
			break
			;;
	esac
done

# usage: file_env VAR [DEFAULT]
#    ie: file_env 'XYZ_DB_PASSWORD' 'example'
# (will allow for "$XYZ_DB_PASSWORD_FILE" to fill in the value of
#  "$XYZ_DB_PASSWORD" from a file, especially for Docker's secrets feature)
file_env() {
	local var="$1"
	local fileVar="${var}_FILE"
	local def="${2:-}"
	if [ "${!var:-}" ] && [ "${!fileVar:-}" ]; then
		echo >&2 "error: both $var and $fileVar are set (but are exclusive)"
		exit 1
	fi
	local val="$def"
	if [ "${!var:-}" ]; then
		val="${!var}"
	elif [ "${!fileVar:-}" ]; then
		val="$(< "${!fileVar}")"
	fi
	export "$var"="$val"
	unset "$fileVar"
}

_check_config() {
	toRun=( "$@" --verbose --help --log-bin-index="$(mktemp -u)" )
	if ! errors="$("${toRun[@]}" 2>&1 >/dev/null)"; then
		cat >&2 <<-EOM

			ERROR: mysqld failed while attempting to check config
			command was: "${toRun[*]}"

			$errors
		EOM
		exit 1
	fi
}

# Fetch value from server config
# We use mysqld --verbose --help instead of my_print_defaults because the
# latter only show values present in config files, and not server defaults
_get_config() {
	local conf="$1"; shift
	"$@" --verbose --help --log-bin-index="$(mktemp -u)" 2>/dev/null | grep "^$conf " | awk '{ print $2 }'
}

# allow the container to be started with `--user`
if [ "$1" = 'mysqld' -a -z "$wantHelp" -a "$(id -u)" = '0' ]; then
	_check_config "$@"
	DATADIR="$(_get_config 'datadir' "$@")"
	mkdir -p "$DATADIR"
	chown -R mysql:mysql "$DATADIR"
	exec gosu mysql "$BASH_SOURCE" "$@"
fi

if [ "$1" = 'mysqld' -a -z "$wantHelp" ]; then
	# still need to check config, container may have started with --user
	_check_config "$@"
	# Get config
	DATADIR="$(_get_config 'datadir' "$@")"

	if [ ! -d "$DATADIR/mysql" ]; then
		# for backward compability support both MYSQL_ and MARIADB_ env vars
		file_env 'MYSQL_ROOT_PASSWORD'
	  file_env 'MARIADB_ROOT_PASSWORD'
		MARIADB_ROOT_PASSWORD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}"
		MARIADB_ALLOW_EMPTY_PASSWORD="${MARIADB_ALLOW_EMPTY_PASSWORD:-$MYSQL_ALLOW_EMPTY_PASSWORD}"
		MARIADB_RANDOM_ROOT_PASSWORD="${MARIADB_RANDOM_ROOT_PASSWORD:-$MYSQL_RANDOM_ROOT_PASSWORD}"
		if [ -z "$MARIADB_ROOT_PASSWORD" -a -z "$MARIADB_ALLOW_EMPTY_PASSWORD" -a -z "$MARIADB_RANDOM_ROOT_PASSWORD" ]; then
			echo >&2 'error: database is uninitialized and password option is not specified '
			echo >&2 '  You need to specify one of MARIADB_ROOT_PASSWORD, MARIADB_ALLOW_EMPTY_PASSWORD and MARIADB_RANDOM_ROOT_PASSWORD'
			exit 1
		fi

		mkdir -p "$DATADIR"

		echo 'Initializing database'
		# "Other options are passed to mysqld." (so we pass all "mysqld" arguments directly here)
		mysql_install_db --auth-root-socket-user=mysql --datadir="$DATADIR" --rpm "${@:2}"
		echo 'Database initialized'

		SOCKET="$(_get_config 'socket' "$@")"
		"$@" --skip-networking --socket="${SOCKET}" &
		pid="$!"

		mysql=( mysql --protocol=socket -umysql -hlocalhost --socket="${SOCKET}" )

		for i in {30..0}; do
			if echo 'SELECT 1' | "${mysql[@]}" &> /dev/null; then
				break
			fi
			echo 'MySQL init process in progress...'
			sleep 1
		done
		if [ "$i" = 0 ]; then
			echo >&2 'MySQL init process failed.'
			exit 1
		fi

		if [ -z "${MARIADB_INITDB_SKIP_TZINFO:-$MYSQL_INITDB_SKIP_TZINFO}" ]; then
			# sed is for https://bugs.mysql.com/bug.php?id=20545
			mysql_tzinfo_to_sql /usr/share/zoneinfo | sed 's/Local time zone must be set--see zic manual page/FCTY/' | "${mysql[@]}" mysql
		fi

		if [ ! -z "$MARIADB_RANDOM_ROOT_PASSWORD" ]; then
            # we have to filter characters like ' and \ that will terminate the sql query or don't count
            # as special characters to keep the enterprise server password policy in mind.
            MARIADB_ROOT_PASSWORD="'"
            while [[ $MARIADB_ROOT_PASSWORD == *"'"* ]] || [[ $MARIADB_ROOT_PASSWORD == *"\\"* ]]; do
			    export MARIADB_ROOT_PASSWORD="$(pwgen -1 32 -y)"
            done
			echo "GENERATED ROOT PASSWORD: $MARIADB_ROOT_PASSWORD"
		fi


		rootCreate=
		# default root to listen for connections from anywhere
		file_env 'MYSQL_ROOT_HOST'
		file_env 'MARIADB_ROOT_HOST' '%'
		MARIADB_ROOT_HOST="${MARIADB_ROOT_HOST:-$MYSQL_ROOT_HOST}"
		if [ ! -z "$MARIADB_ROOT_HOST" -a "$MARIADB_ROOT_HOST" != 'localhost' ]; then
			# no, we don't care if read finds a terminating character in this heredoc
			# https://unix.stackexchange.com/questions/265149/why-is-set-o-errexit-breaking-this-read-heredoc-expression/265151#265151
			read -r -d '' rootCreate <<-EOSQL || true
				CREATE USER 'root'@'${MARIADB_ROOT_HOST}' IDENTIFIED BY '${MARIADB_ROOT_PASSWORD}' ;
				GRANT ALL ON *.* TO 'root'@'${MARIADB_ROOT_HOST}' WITH GRANT OPTION ;
			EOSQL
		fi

		"${mysql[@]}" <<-EOSQL
			-- What's done in this file shouldn't be replicated
			-- or products like mysql-fabric won't work
			SET @@SESSION.SQL_LOG_BIN=0;

			DELETE FROM mysql.user WHERE user NOT IN ('mysql.sys', 'mysqlxsys', 'root', 'mysql') OR host NOT IN ('localhost') ;
			SET PASSWORD FOR 'root'@'localhost'=PASSWORD('${MARIADB_ROOT_PASSWORD}') ;
			GRANT ALL ON *.* TO 'root'@'localhost' WITH GRANT OPTION ;
			${rootCreate}
			DROP DATABASE IF EXISTS test ;
			FLUSH PRIVILEGES ;
		EOSQL

		if [ ! -z "$MARIADB_ROOT_PASSWORD" ]; then
			mysql+=( -p"${MARIADB_ROOT_PASSWORD}" )
		fi

		file_env 'MYSQL_DATABASE'
		file_env 'MARIADB_DATABASE'
		MARIADB_DATABASE="${MARIADB_DATABASE:-$MYSQL_DATABASE}"
		if [ "$MARIADB_DATABASE" ]; then
			echo "CREATE DATABASE IF NOT EXISTS \`$MARIADB_DATABASE\` ;" | "${mysql[@]}"
			mysql+=( "$MARIADB_DATABASE" )
		fi

		file_env 'MYSQL_USER'
		file_env 'MARIADB_USER'
		MARIADB_USER="${MARIADB_USER:-$MYSQL_USER}"
		file_env 'MYSQL_PASSWORD'
		file_env 'MARIADB_PASSWORD'
		MARIADB_PASSWORD="${MARIADB_PASSWORD:-$MYSQL_PASSWORD}"
		if [ "$MARIADB_USER" -a "$MARIADB_PASSWORD" ]; then
			echo "CREATE USER '$MARIADB_USER'@'%' IDENTIFIED BY '$MARIADB_PASSWORD' ;" | "${mysql[@]}"

			if [ "$MARIADB_DATABASE" ]; then
				echo "GRANT ALL ON \`$MARIADB_DATABASE\`.* TO '$MARIADB_USER'@'%' ;" | "${mysql[@]}"
			fi
		fi

		echo
		for f in /docker-entrypoint-initdb.d/*; do
			case "$f" in
				*.sh)     echo "$0: running $f"; . "$f" ;;
				*.sql)    echo "$0: running $f"; "${mysql[@]}" < "$f"; echo ;;
				*.sql.gz) echo "$0: running $f"; gunzip -c "$f" | "${mysql[@]}"; echo ;;
				*)        echo "$0: ignoring $f" ;;
			esac
			echo
		done

		if ! kill -s TERM "$pid" || ! wait "$pid"; then
			echo >&2 'MySQL init process failed.'
			exit 1
		fi

		echo
		echo 'MySQL init process done. Ready for start up.'
		echo
	fi
fi

exec "$@"


