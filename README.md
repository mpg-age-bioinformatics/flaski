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
