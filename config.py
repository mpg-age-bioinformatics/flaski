import os
import secrets
import redis

basedir = os.path.abspath(os.path.dirname(__file__))

with open(basedir+"/.git/refs/heads/master", "r") as f:
    commit=f.readline().split("\n")[0]

class Config(object):
    USERS_DATA = os.environ.get('USERS_DATA') or "/flaski_data/users/"
    LOGS=os.environ.get('LOGS') or '/flaski_data/logs/'
    session_token=secrets.token_urlsafe(16)
    SECRET_KEY = os.environ.get('SECRET_KEY') or session_token
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'redis'
    redis_password = os.environ.get('REDIS_PASSWORD') or 'REDIS_PASSWORD'
    REDIS_ADDRESS = os.environ.get('REDIS_ADDRESS') or '127.0.0.1:6379/0'
    SESSION_REDIS = redis.from_url('redis://:%s@%s' %(redis_password,REDIS_ADDRESS))
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_ROOT_PASSWORD = os.environ.get('MYSQL_ROOT_PASSWORD') or 'mypass'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'mariadb'
    MYSQL_PORT = os.environ.get('MYSQL_PORT') or '3306'
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://%s:%s@%s:%s/flaski' %(MYSQL_USER,MYSQL_ROOT_PASSWORD,MYSQL_HOST,MYSQL_PORT)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 8025)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = os.environ.get('ADMINS').split(",") or ['jboucas@age.mpg.de']
    PRIVATE_APPS = os.environ.get('PRIVATE_APPS') or None
    COMMIT = commit