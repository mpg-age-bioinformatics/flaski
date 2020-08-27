from flask import Flask, make_response, request, session, render_template, send_file, Response, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask.views import MethodView
from werkzeug import secure_filename
from datetime import datetime
from flaski import db
import humanize
import os
import re
import stat
import json
import mimetypes
import sys
from pathlib2 import Path
from copy import copy
import shutil
import io
from flaski.routes import FREEAPPS
from flaski.forms import SettingsForm


from flaski.routines import session_to_file
from flaski import app, sess

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def userspace():
    apps=current_user.user_apps
    form = SettingsForm()

    if form.validate_on_submit():
        current_user.multipleapps=form.multipleapps.data
        current_user.notifyme=form.notifyme.data
        db.session.add(current_user)
        db.session.commit()

    form.multipleapps.data=current_user.multipleapps
    form.notifyme.data=current_user.notifyme

    return render_template('/settings.html', form=form, apps=apps)

