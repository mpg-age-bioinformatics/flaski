# flaski

## Deploying flaski

Create local folders:
```
mkdir -p ~/flaski23/backup/stats ~/flaski23/backup/users_data2 ~/flaski23/backup/users_data3 ~/flaski23/backup/mariadb ~/flaski23/private ~/flaski23/mpcdf ~/flaski23/submissions
```

For production export secret variables into `.env`:
```bash
cat << EOF > .env.prod
MAIL_PASSWORD="<mail password>"
MYSQL_PASSWORD=$(openssl rand -base64 20)
MYSQL_ROOT_PASSWORD=$(openssl rand -base64 20)
REDIS_PASSWORD=$(openssl rand -base64 20)
SECRET_KEY=$(openssl rand -base64 20)
EOF
```

For local development (quote all mail related entries in the `docker-compose.yml`).

To deploy flaski edit the `docker-compose.yml` accordingly and then:
```bash
docker-compose -f production-compose.yml up
```
Check the `stdout` with:
```bash
docker-compose logs
```
or for example:
```bash
docker-compose logs -f server
```
If running myapp on development mode you will have to start flask from inside the server container:
```
docker-compose exec server3 /bin/bash
flask run --host 0.0.0.0 --port 8000
```
Adding administrator user:
```
docker-compose run --entrypoint="python3 /myapp/myapp.py admin --add myemail@gmail.com" init 
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

## Backups

```bash
docker-compose exec backup /backup.sh
docker-compose exec backup rsync -rtvh --delete /myapp_data/users/ /backup/users_data/
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
make the required imports:
```python
from myapp import app, db
from myapp.models import User, UserLogging
```
and then for removing a user from the db:
```python
u=User.query.filter_by(email=<user_email>).first()
db.session.delete(u)
db.session.commit()
```
for editing entries eg.:
```python
user=User.query.filter_by(email=<user_email>).first()
user.active = False
db.session.add(user)
db.session.commit()
```

Collecting usage entries:
```bash
docker-compose run --entrypoint="python3 /myapp/myapp.py stats /backup/stats" init
```

If you need to re-initiate your database
```bash
rm -rf migrations && flask db init && flask db migrate -m "users table" && flask db upgrade 
```

upgrading
```bash
flask db migrate -m "new fields in user model"
flask db upgrade
```

Manually backup a database:
```bash
docker-compose exec mariadb /usr/bin/mysqldump -u root --password=mypass ${APP_NAME} > dump.sql
```

Manually restore a database from backup:
```bash
cat dump.sql | docker-compose exec mariadb mysql --user=root --password=mypass ${APP_NAME}
```

## Multiplatform builds

Builds are currently working for `linux/amd64` and `linux/arm64` but not for `linux/arm/v7`.

```
docker buildx create --name mybuilder
docker buildx use mybuilder
docker buildx inspect --bootstrap
docker buildx build --platform linux/amd64,linux/arm64,linux/arm/v7 --build-arg MYAPP_VERSION=local --no-cache --force-rm -t myapp/myapp:latest -f services/server/Dockerfile . --load
```

To push result image into registry use --push or to load image into docker use --load.

## Annual email validation

The daily job lives in the myapp repository at `utils/email_revalidation.py`.
The myapp image already copies `utils`, providing `/myapp/utils/email_revalidation.py`.
It requires the updated `myapp` package containing
`myapp/email_revalidation.py` and the email lifecycle fields in `User`. Rebuild
and deploy the myapp base image as well as the flaski image; updating flaski alone
is insufficient.

Before deploying the new model, back up the database and add the four nullable
columns using the old application's configured container. This script is
idempotent and does not send emails or alter passwords:

```bash
docker compose -f production-compose.yml cp /Users/jboucas/myapp/utils/migrate_email_revalidation.py server3:/myapp/utils/migrate_email_revalidation.py
docker compose -f production-compose.yml exec -T server3 python3 /myapp/utils/migrate_email_revalidation.py
```

If your deployments track schema changes through Alembic, also reconcile these
columns with that deployment's migration history. No Alembic revision is supplied
because this repository has no committed baseline migration history.

After deploying both images, verify the counts without making any changes:

```bash
docker compose -f production-compose.yml exec -T server3 python3 /myapp/utils/email_revalidation.py --dry-run
```

Schedule the Python command daily through a Kubernetes CronJob using the server
image, database/mail/secret configuration, and appropriate mounts. The deployment
guide in the bit_k8_tf repository (`wiki/email-revalidation-deployment.md`) covers
creating and enabling the CronJob. Do not run it through every web worker.
Per-user database row locks prevent overlapping scheduler runs from mailing the
same user twice in normal operation.

The lifecycle uses UTC database timestamps:

- Active users whose latest validation (or original `confirmed_on`) is more than
  one calendar year old receive a token link. For users with no validation date,
  registration more than one year ago triggers the request.
- `email_validation_first_sent_on` starts a new cycle;
  `email_validation_last_sent_on` records the latest successfully submitted email.
- At seven days, one reminder is sent. At fourteen days from the first email,
  an unvalidated user's password is replaced with an unknown random password,
  and `email_deactivated_on` is recorded. A deactivation email explains recovery.
  If the scheduler missed the reminder entirely, it sends that reminder before
  deactivating on a subsequent daily run.
- A valid, current-cycle link records `email_validated_on` and ends the cycle.
  Tokens cannot be used for password reset, for a changed email address, or reused
  after validation. Existing registration/reset links that relied on their old
  shared token purpose must be replaced with newly issued links after deployment.
- Deactivated users are excluded from mail runs and their existing login sessions
  are rejected. The administrative `active` flag stays unchanged so password
  recovery remains available. Recovery changes the password; only a subsequent
  successful login (including enabled 2FA) clears `email_deactivated_on` and
  records fresh email validation, since recovery proves email access.

Mail is sent synchronously; a failed SMTP submission does not advance the cycle
or deactivate an account. Failures are retried on the next run, and the command
returns a nonzero status if any user failed. SMTP acceptance and database commit
are separate operations: a process crash or database commit failure after SMTP
acceptance can cause a repeated email on retry. No validation token or password
is intentionally written to the lifecycle job's logs.

The schema changes, cron installation, and live email run are deployment steps;
creating these files does not enable the job automatically.
