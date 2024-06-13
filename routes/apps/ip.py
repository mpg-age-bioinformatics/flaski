from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_options, GROUPS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import base64
import pandas as pd
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename
from flask import jsonify, request
import requests
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# @app.route('/v3/ip', methods=['GET'])
# def get_tasks():
#     if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
#         return jsonify({'REMOTE_ADDR': request.environ['REMOTE_ADDR']}), 200
#     else:
#         return jsonify({'REMOTE_ADDR': request.environ['REMOTE_ADDR'],'HTTP_X_FORWARDED_FOR': request.environ['HTTP_X_FORWARDED_FOR']}), 200


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("ip",url_base_pathname=f'{PAGE_PREFIX}/ip/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"],  assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/") update_title='Load...', 

protect_dashviews(dashapp)

if app.config["SESSION_TYPE"] == "sqlalchemy":
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"] , echo=True)
    app.config["SESSION_SQLALCHEMY"] = engine
elif app.config["CACHE_TYPE"] == "RedisCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
    })
elif app.config["CACHE_TYPE"] == "RedisSentinelCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [ 
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), os.environ.get('CACHE_REDIS_SENTINELS_port') ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    ip_site1 = requests.get('https://checkip.amazonaws.com').text.strip()
    ip_site2 = requests.get('https://ifconfig.me').text.strip()
    ip_site3 = requests.get('https://ident.me').text.strip()
    headers_list = request.headers.getlist("HTTP_X_FORWARDED_FOR")
    ip = headers_list[0] if headers_list else request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
    l=request.headers.getlist("X-Forwarded-For")
    l="--".join(l)
    r=request.access_route
    r="--".join(r)
    return ["r::", r, "//", "l::", l, "//", "X-Real-IP", request.headers['X-Real-IP'], "//","ip::", ip, "//" ,'REMOTE_ADDR', '\n', request.environ['REMOTE_ADDR'],'\n', 'HTTP_X_FORWARDED_FOR', '\n', request.environ['HTTP_X_FORWARDED_FOR'], '\n', 'x_real_ip::', request.headers.get('X-Real-IP'), '\n', 'remote_addr::', request.remote_addr, '\n', 'ip1::', ip_site1, '\n', 'ip2::', ip_site2, '\n', 'ip3::', ip_site3 ]
    # if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
    #     return [ 'REMOTE_ADDR','\n', request.environ['REMOTE_ADDR'] ]
    # else:
    #     return [ 'REMOTE_ADDR', '\n', request.environ['REMOTE_ADDR'],'\n', 'HTTP_X_FORWARDED_FOR', '\n', request.environ['HTTP_X_FORWARDED_FOR'] ]