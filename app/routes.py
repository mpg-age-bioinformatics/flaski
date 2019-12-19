from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from app import app
from werkzeug.utils import secure_filename
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, UserLogging
from app.forms import RegistrationForm
from datetime import datetime
from app import db
from werkzeug.urls import url_parse
from app.forms import ResetPasswordRequestForm
from app.email import send_password_reset_email, send_validate_email
from app.forms import ResetPasswordForm
#from app.token import generate_confirmation_token, confirm_token
from app.plots.figures.scatterplot import make_figure, figure_defaults

import os
import io
import sys
import random
import json

import matplotlib
matplotlib.use('agg')
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.backends.backend_svg import FigureCanvasSVG
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import mpld3

import pandas as pd

import base64

@app.route('/', methods=['GET', 'POST'])
def landingpage():
    return redirect(url_for('login'))

# @app.route('/login',defaults={'width': None, 'height': None}, methods=['GET', 'POST'])
# @app.route('/login/<width>/<height>',methods=['GET', 'POST'])
@app.route('/login',methods=['GET', 'POST'])
def login(width=None, height=None):
    # if not width or not height:
    #     return """
    #     <script>
    #     (() => window.location.href = window.location.href +
    #     ['', window.innerWidth, window.innerHeight].join('/'))()
    #     </script>
    #     """
    if current_user.is_authenticated:
        return redirect(url_for('scatterplot'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        # session["width"]=width
        # session["height"]=height
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('scatterplot')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('scatterplot'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(firstname=form.firstname.data,\
                lastname=form.lastname.data,\
                email=form.email.data,\
                organization=form.organization.data)
        user.set_password(form.password.data)
        user.registered_on=datetime.utcnow()
        db.session.add(user)
        db.session.commit()
        send_validate_email(user)
        flash('Please check your email and confirm your account.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/confirm/<token>')
def confirm(token):
    user = User.verify_email_token(token)
    if not user:
        return redirect(url_for('login'))
    user = User.verify_email_token(token)
    if user.active:
        flash('Account already confirmed. Please login.', 'success')
    else:
        user.active = True
        user.confirmed_on = datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')
    return redirect(url_for('login'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('scatterplot'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('scatterplot'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('scatterplot'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password_set=datetime.utcnow()
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
        if not current_user.active:
            flash('This account is not active. Please contact support.')
            logout_user()
            return redirect(url_for('login'))

from flask import Flask, make_response, request, session, render_template, send_file, Response
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

root = os.path.normpath("/tmp")
key = "my_trusted_key"

ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
datatypes = {'audio': 'm4a,mp3,oga,ogg,webma,wav', 'archive': '7z,zip,rar,gz,tar', 'image': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'pdf': 'pdf', 'quicktime': '3g2,3gp,3gp2,3gpp,mov,qt', 'source': 'atom,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml,plist', 'text': 'txt', 'video': 'mp4,m4v,ogv,webm', 'website': 'htm,html,mhtm,mhtml,xhtm,xhtml'}
icontypes = {'fa-music': 'm4a,mp3,oga,ogg,webma,wav', 'fa-archive': '7z,zip,rar,gz,tar', 'fa-picture-o': 'gif,ico,jpe,jpeg,jpg,png,svg,webp', 'fa-file-text': 'pdf', 'fa-film': '3g2,3gp,3gp2,3gpp,mov,qt', 'fa-code': 'atom,plist,bat,bash,c,cmd,coffee,css,hml,js,json,java,less,markdown,md,php,pl,py,rb,rss,sass,scpt,swift,scss,sh,xml,yml', 'fa-file-text-o': 'txt', 'fa-film': 'mp4,m4v,ogv,webm', 'fa-globe': 'htm,html,mhtm,mhtml,xhtm,xhtml'}

@app.template_filter('size_fmt')
def size_fmt(size):
    return humanize.naturalsize(size)

@app.template_filter('time_fmt')
def time_desc(timestamp):
    mdate = datetime.fromtimestamp(timestamp)
    str = mdate.strftime('%Y-%m-%d %H:%M:%S')
    return str

@app.template_filter('data_fmt')
def data_fmt(filename):
    t = 'unknown'
    for type, exts in datatypes.items():
        if filename.split('.')[-1] in exts:
            t = type
    return t

@app.template_filter('icon_fmt')
def icon_fmt(filename):
    i = 'fa-file-o'
    for icon, exts in icontypes.items():
        if filename.split('.')[-1] in exts:
            i = icon
    return i

@app.template_filter('humanize')
def time_humanize(timestamp):
    mdate = datetime.utcfromtimestamp(timestamp)
    return humanize.naturaltime(mdate)

def get_type(mode):
    if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        type = 'dir'
    else:
        type = 'file'
    return type

def partial_response(path, start, end=None):
    file_size = os.path.getsize(path)

    if end is None:
        end = file_size - start - 1
    end = min(end, file_size - 1)
    length = end - start + 1

    with open(path, 'rb') as fd:
        fd.seek(start)
        bytes = fd.read(length)
    assert len(bytes) == length

    response = Response(
        bytes,
        206,
        mimetype=mimetypes.guess_type(path)[0],
        direct_passthrough=True,
    )
    response.headers.add(
        'Content-Range', 'bytes {0}-{1}/{2}'.format(
            start, end, file_size,
        ),
    )
    response.headers.add(
        'Accept-Ranges', 'bytes'
    )
    return response

def get_range(request):
    range = request.headers.get('Range')
    m = re.match('bytes=(?P<start>\d+)-(?P<end>\d+)?', range)
    if m:
        start = m.group('start')
        end = m.group('end')
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None

class PathView(MethodView):
    def get(self, p=''):
        hide_dotfile = request.args.get('hide-dotfile', request.cookies.get('hide-dotfile', 'no'))

        path = os.path.join(root, p)

        if os.path.isdir(path):
            contents = []
            total = {'size': 0, 'dir': 0, 'file': 0}
            for filename in os.listdir(path):
                if filename in ignored:
                    continue
                if hide_dotfile == 'yes' and filename[0] == '.':
                    continue
                filepath = os.path.join(path, filename)
                stat_res = os.stat(filepath)
                info = {}
                info['name'] = filename
                info['mtime'] = stat_res.st_mtime
                ft = get_type(stat_res.st_mode)
                info['type'] = ft
                total[ft] += 1
                sz = stat_res.st_size
                info['size'] = sz
                total['size'] += sz
                contents.append(info)
            page = render_template('fileserver.html', path=p, contents=contents, total=total, hide_dotfile=hide_dotfile)
            res = make_response(page, 200)
            res.set_cookie('hide-dotfile', hide_dotfile, max_age=16070400)
        elif os.path.isfile(path):
            if 'Range' in request.headers:
                start, end = get_range(request)
                res = partial_response(path, start, end)
            else:
                res = send_file(path)
                res.headers.add('Content-Disposition', 'attachment')
        else:
            res = make_response('Not found', 404)
        return res

    def post(self, p=''):
        if request.cookies.get('auth_cookie') == key:
            path = os.path.join(root, p)
            Path(path).mkdir(parents=True, exist_ok=True)

            info = {}
            if os.path.isdir(path):
                files = request.files.getlist('files[]')
                for file in files:
                    try:
                        filename = secure_filename(file.filename)
                        file.save(os.path.join(path, filename))
                    except Exception as e:
                        info['status'] = 'error'
                        info['msg'] = str(e)
                    else:
                        info['status'] = 'success'
                        info['msg'] = 'File Saved'
            else:
                info['status'] = 'error'
                info['msg'] = 'Invalid Operation'
            res = make_response(json.JSONEncoder().encode(info), 200)
            res.headers.add('Content-type', 'application/json')
        else:
            info = {} 
            info['status'] = 'error'
            info['msg'] = 'Authentication failed'
            res = make_response(json.JSONEncoder().encode(info), 401)
            res.headers.add('Content-type', 'application/json')
        return res

path_view = PathView.as_view('path_view')
app.add_url_rule('/fileserver', view_func=path_view)
app.add_url_rule('/fileserver/<path:p>', view_func=path_view)
