from flask import Flask, make_response, request, session, render_template, send_file, Response, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from flask.views import MethodView
from werkzeug import secure_filename
from datetime import datetime
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


from flaski.routines import session_to_file
from flaski import app, sess

@app.route('/userspace', methods=['GET', 'POST'])
@login_required
def userspace():
    apps=current_user.user_apps
    return render_template('/userspace.html', apps=apps)

