# CONTRIBUTING

For additional info please check the `myapp` repository.

Clone flaski and the base myapp repo:

```
cd ~
git clone git@github.com:mpg-age-bioinformatics/myapp.git
git clone git@github.com:mpg-age-bioinformatics/flaski.git
```

Create secret variables once, preserving an existing `.env`:

```
cd ~/flaski
if [ ! -e .env ]; then
  (umask 077
   cat << EOF > .env
MYSQL_PASSWORD=$(openssl rand -hex 24)
MYSQL_ROOT_PASSWORD=$(openssl rand -hex 24)
REDIS_PASSWORD=$(openssl rand -hex 24)
SECRET_KEY=$(openssl rand -hex 32)
EOF
  )
fi
```

Do not regenerate these credentials when reusing an existing database volume.
MariaDB retains the original password; changing `.env` can cause `Access denied`.
Restore the original credentials if this happens, or see
[Troubleshooting local deployment](#troubleshooting-local-deployment) for a clean
reset if you do not need the existing local data.

Create local folders:
```
mkdir -p ~/flaski23/backup/stats ~/flaski23/backup/users_data2 ~/flaski23/backup/users_data3 ~/flaski23/backup/mariadb ~/flaski23/private ~/flaski23/mpcdf ~/flaski23/submissions
```

For local development, adjust `docker-compose.yml` to your local paths, then
initialize pyflaski:

```bash
cd ~/flaski
git submodule update --init --recursive
```

Then choose one of the following options.

Build the images locally:

```bash
docker-compose up -d --build
```

Or download the published images from Docker Hub and start without building:

```bash
docker-compose pull
docker-compose up -d --no-build
```

This still requires the local folders and initialized submodule above, followed
by the development server command below. Mounted source files use the Python
dependencies provided by the downloaded images; build locally if your changes
require different dependencies.

Run all commands in this guide from `~/flaski`, using `docker-compose.yml`.
With Compose v2, use `docker compose` in place of `docker-compose` throughout.

If running myapp on development mode you will have to start flask from inside the server container:
```
docker-compose exec server3 /bin/bash
flask run --host 0.0.0.0 --port 8000
```
Optionally, you can add the following line to your `/etc/hosts`
```
127.0.0.1       flaski.localhost
```

You can now access flaski over https://flaski.localhost/v3.

### Troubleshooting local deployment

If deployment gets stuck on `Waiting for mysql..` with `Access denied` errors,
or login fails with database authentication errors after a previous setup, the
database volume may still contain older credentials.

If you are happy to reset the local setup, run before deploying with docker compose again:

```bash
cd ~/flaski
docker-compose down -v
```

**This deletes the stack's volumes, including the local database, accounts, and
user files stored in those volumes.** Files mounted from your laptop are not
deleted. This reset addresses stale local database state; it does not fix image build
errors or an unresponsive Docker engine.

### Email logging

Keep the default local email settings in `docker-compose.yml`. The SMTP debugging
server listens on `localhost:8025` and prints emails, including account confirmation
links, to the terminal instead of sending them.
To run this server, open a second terminal session and run the following command on it:
```bash
docker-compose exec server3 python3 -m smtpd -n -c DebuggingServer localhost:8025
```

Leave this terminal running, open the app's Register page, and create an account.
The confirmation email will appear in this terminal. Copy its activation link
into your browser to confirm your account, then log in.

If you need administrator access, run the following in another terminal,
replacing `myemail@gmail.com` with the email you registered:
```
docker-compose run --entrypoint="python3 /myapp/myapp.py admin --add myemail@gmail.com" init
```

### Editing apps

The development configuration mounts `routes/apps` and `pyflaski/pyflaski` from
your checkout into the container. Edit these files locally; no image rebuild is
needed for Python code changes in those mounts. Flask's debug reloader normally
picks up changes.

Rebuild when changing image contents such as installed dependencies or files
that are not mounted. Private datasets belong under `~/flaski23/private`, mounted
at `/flaski_private`.

### pyflaski

pyflaski was added as a submodule of flaski:
```
cd ~/flaski
git submodule add git@github.com:mpg-age-bioinformatics/pyflaski.git pyflaski
git submodule init pyflaski
```

If making a fresh clone you will need to:
```
cd ~/flaski
git submodule update --init --recursive
```

To update from the remote:
```
git submodule update --recursive --remote
```

Commiting changes:
```
cd ~/flaski/pyflaski
git add -A . 
git commit -m "<describe your changes here>"
git push origin HEAD:master
```

then tell the main project to start tracking the updated version:
```
cd ~/flaski
git add pyflaski
git commit -m pyflaski
git push
```
