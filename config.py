import os
import secrets
import redis
basedir = os.path.abspath(os.path.dirname(__file__))

with open(basedir+"/.git/refs/heads/master", "r") as f:
    commit=f.readline()

class Config(object):
    session_token=secrets.token_urlsafe(16)
    SECRET_KEY = os.environ.get('SECRET_KEY') or session_token
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'redis'
    redis_password = os.environ.get('REDIS_PASSWORD') or 'REDIS_PASSWORD'
    SESSION_REDIS = redis.from_url('redis://:%s@127.0.0.1:6379/0' %redis_password)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ['jboucas@age.mpg.de']
    COMMIT = commit