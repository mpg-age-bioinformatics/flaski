from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from flaski.models import User, UserLogging
from flaski.forms import RegistrationForm
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.forms import ResetPasswordRequestForm
from flaski.email import send_password_reset_email, send_validate_email
from flaski.forms import ResetPasswordForm
#from app.token import generate_confirmation_token, confirm_token
from flaski.plots.figures.scatterplot import make_figure, figure_defaults

import os
import io
import sys
import random
import json

# import matplotlib
# matplotlib.use('agg')
# from matplotlib.backends.backend_agg import FigureCanvasAgg
# from matplotlib.backends.backend_svg import FigureCanvasSVG
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
# import mpld3

import pandas as pd

import base64

FREEAPPS=[{ "name":"Scatter plot","id":'scatterplot_more', "link":'scatterplot' , "java":"javascript:ReverseDisplay('scatterplot_more')", "description":"A static scatterplot app." },\
    { "name":"iScatter plot", "id":'iscatterplot_more',"link":'scatterplot' ,"java":"javascript:ReverseDisplay('iscatterplot_more')", "description":"An intreactive scatterplot app."} ]


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    apps=FREEAPPS
    if current_user.is_authenticated:
        apps=apps+session["PRIVATE_APPS"]
        return render_template('index.html',userlogged="yes", apps=apps)
    else:
        return render_template('index.html',userlogged="no",apps=apps)  # https://flaski.mpg.de/%7B%7B%20url_for('scatterplot')%20%7D%7D
    #return redirect(url_for('login'))

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
    def read_private_apps(useremail):
        PRIVATE_APPS=[]
        if app.config['PRIVATE_APPS']:
            df=pd.read_csv(app.config['PRIVATE_APPS'],index_col="app",sep="\t")
            df=df.transpose()
            dic=df.to_dict()
            for entry in list(dic.keys()):
                private_app=dic[entry]
                allowed=private_app["allowed"].split(",")
                if "all" in allowed:
                    del(private_app["allowed"])
                    PRIVATE_APPS.append(private_app)
                elif useremail in allowed:
                    del(private_app["allowed"])
                    PRIVATE_APPS.append(private_app)
                elif len([ s for s in allowed if s[0] == "#" ]) > 0 :
                    for domain in [ s for s in allowed if s[0] == "#" ]:
                        if domain[1:] in useremail:
                            del(private_app["allowed"])
                            PRIVATE_APPS.append(private_app)
                            break
        return PRIVATE_APPS

    if current_user.is_authenticated:
        session["PRIVATE_APPS"]=read_private_apps(current_user.email)
        return redirect(url_for('index'))
        
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
            next_page = url_for('index')
        session["PRIVATE_APPS"]=read_private_apps(current_user.email)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        return redirect(url_for('index'))
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
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
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

@app.route('/reset_plot')
@login_required
def reset_plot():
    app=session["app"]
    session["app"]=None
    return redirect(url_for(app))
