import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import os
from flask_mail import Mail
from flask_session import Session
from waitress import serve

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app ,engine_options={"pool_pre_ping":True, "pool_size":0,"pool_recycle":-1} )
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
sess = Session()
sess.init_app(app)

#wsgi_app = app.wsgi_app

from flaski import routes, models, errors, storage

from flaski.apps.routes import scatterplot, iscatterplot, heatmap, iheatmap, venndiagram, icellplot, david, aarnaseqlake

if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr=app.config['ADMINS'][0],
            toaddrs=app.config['ADMINS'], subject='%s :: Flaski Failure' %(app.config['INSTANCE']),
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists(app.config['LOGS']):
        os.mkdir(app.config['LOGS'])
    file_handler = RotatingFileHandler(app.config['LOGS']+'flaski.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Flaski startup')

# if __name__ == "__main__":
#    #app.run() ##Replaced with below code to run it using waitress 
#    serve(app, host='0.0.0.0', port=8000)