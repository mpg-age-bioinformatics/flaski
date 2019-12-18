# flask_dashboard

### redis

starting redis:

```
redis-server redis.conf
```

### Databases

```
rm -rf app.db migrations
flask db init
flask db migrate -m "users table"
flask db upgrade 
```

alternative
```
flask db migrate -m "new fields in user model"
flask db upgrade
```

### Logging

There are two approaches to test email logging. The easiest one is to use the SMTP debugging server from Python. 
This is a fake email server that accepts emails, but instead of sending them, it prints them to the console. 
To run this server, open a second terminal session and run the following command on it:
```
python -m smtpd -n -c DebuggingServer localhost:8025 
```
and 
```
export MAIL_SERVER=localhost
export MAIL_PORT=8025
```
before running your app.

A second testing approach for this feature is to configure a real email server. 
Below is the configuration to use your Gmail account's email server:
```
export MAIL_SERVER=smtp.googlemail.com
export MAIL_PORT=587
export MAIL_USE_TLS=1
export MAIL_USERNAME=<your-gmail-username>
export MAIL_PASSWORD=<your-gmail-password>
```