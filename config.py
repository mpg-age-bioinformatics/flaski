import os
import secrets
import redis

class Config(object):
    session_token=secrets.token_urlsafe(16)
    SECRET_KEY = os.environ.get('SECRET_KEY') or session_token
    SESSION_TYPE = os.environ.get('SESSION_TYPE') or 'redis'
    redis_password = os.environ.get('REDIS_PASSWORD') or 'REDIS_PASSWORD'
    SESSION_REDIS = redis.from_url('redis://:%s@127.0.0.1:6379/0' %redis_password)