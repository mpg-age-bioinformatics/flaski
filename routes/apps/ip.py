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

@app.route('/v3/ip', methods=['GET'])
def get_tasks():
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return jsonify({'REMOTE_ADDR': request.environ['REMOTE_ADDR']}), 200
    else:
        return jsonify({'REMOTE_ADDR': request.environ['REMOTE_ADDR'],'HTTP_X_FORWARDED_FOR': request.environ['HTTP_X_FORWARDED_FOR']}), 200
