import os
import secrets
import redis
basedir = os.path.abspath(os.path.dirname(__file__))

with open(basedir+"/.git/refs/heads/master", "r") as f:
    commit=f.readline().split("\n")[0]

class Config(object):
    session_token=secrets.token_urlsafe(16)
    SECRET_KEY = os.environ.get('SECRET_KEY') or session_token
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'redis'
    redis_password = os.environ.get('REDIS_PASSWORD') or 'REDIS_PASSWORD'
    REDIS_ADDRESS = os.environ.get('REDIS_ADDRESS') or '127.0.0.1:6379/0'
    SESSION_REDIS = redis.from_url('redis://:%s@%s' %(redis_password,REDIS_ADDRESS))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://flaski:flaskidbpass@localhost:3306/flaski' #'sqlite:///' + os.path.join('/flaski_data/data/', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['jboucas@age.mpg.de']
    COMMIT = commit