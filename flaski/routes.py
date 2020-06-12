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
from flaski.email import send_password_reset_email, send_validate_email, send_help_email
from flaski.forms import ResetPasswordForm
from flaski.routines import session_to_file
#from app.token import generate_confirmation_token, confirm_token
#from flaski.plots.figures.scatterplot import make_figure, figure_defaults
from flaski.routines import read_private_apps, reset_all

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
        { "name":"iScatter plot", "id":'iscatterplot_more',"link":'iscatterplot' ,"java":"javascript:ReverseDisplay('iscatterplot_more')", "description":"An intreactive scatterplot app."},\
        { "name":"Heatmap", "id":'heatmap_more',"link":'heatmap' ,"java":"javascript:ReverseDisplay('heatmap_more')", "description":"An heatmap plotting app."},\
        { "name":"iHeatmap", "id":'iheatmap_more',"link":'iheatmap' ,"java":"javascript:ReverseDisplay('iheatmap_more')", "description":"An interactive heatmap plotting app."},\
        { "name":"Venn diagram", "id":'venndiagram_more',"link":'venndiagram' ,"java":"javascript:ReverseDisplay('venndiagram_more')", "description":"A venn diagram plotting app."},\
        { "name":"DAVID", "id":'david_more',"link":'david' ,"java":"javascript:ReverseDisplay('david_more')", "description":"A DAVID querying plot."},\
        { "name":"iCell plot", "id":'icellplot_more',"link":'icellplot' ,"java":"javascript:ReverseDisplay('icellplot_more')", "description":"A DAVID reporting plot."},\
        { "name":"Histogram", "id":'histogram_more',"link":'histogram' ,"java":"javascript:ReverseDisplay('histogram_more')", "description":"A Histogram plot."}]

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        apps=current_user.user_apps
        return render_template('index.html',userlogged="yes", apps=apps, ashtag=app.config['COMMIT'][:7], instance=app.config['INSTANCE'])
    else:
        return render_template('index.html',userlogged="no",apps=FREEAPPS,ashtag=app.config['COMMIT'][:7], instance=app.config['INSTANCE'])  # https://flaski.mpg.de/%7B%7B%20url_for('scatterplot')%20%7D%7D
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
    if current_user.is_authenticated:
        # session["PRIVATE_APPS"]=read_private_apps(current_user.email,app)
        return redirect(url_for('index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        session.permanent = form.remember_me.data
        next_page = request.args.get('next')
        #session["APPS"]=FREEAPPS
        user.user_apps=FREEAPPS+read_private_apps(current_user.email,app)
        db.session.add(user)
        db.session.commit()
        # session["width"]=width
        # session["height"]=height
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        # session["PRIVATE_APPS"]=read_private_apps(current_user.email,app)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    session.clear()
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
                privacy=form.privacy.data,\
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

@app.route('/reset')
@login_required
def reset():
    if 'app' in list(session.keys()):
        page=session["app"]
    else:
        page="index"
    reset_all(session)
    #session["app"]='reset'
    return redirect(url_for(page))

@app.route('/download/<json_type>', methods=['GET','POST'])
@login_required
def download(json_type="arg"):
    # READ INPUT DATA FROM SESSION JSON
    session_=session_to_file(session,json_type)

    session_file = io.BytesIO()
    session_file.write(json.dumps(session_).encode())
    session_file.seek(0)

    plot_arguments=session["plot_arguments"]

    eventlog = UserLogging(email=current_user.email,action="download %s %s" %(json_type, session["app"]))
    db.session.add(eventlog)
    db.session.commit()

    return send_file(session_file, mimetype='application/json', as_attachment=True, attachment_filename=plot_arguments["session_argumentsn"]+"."+json_type )

@app.route('/help', methods=['GET','POST'])
@login_required
def askforhelp():
    import tempfile
    page=session["app"]
    tb_str=session["traceback"]

    session_=session_to_file(session,"ses")
    if not os.path.isdir(app.config['USERS_DATA']+"/tmp/"):
        os.makedirs(app.config['USERS_DATA']+"/tmp/")
    
    session_file_name=tempfile.mkstemp(dir=app.config['USERS_DATA']+"/tmp/",suffix='.ses')[1]
    with open(session_file_name, "w") as session_file:
        json.dump(session_, session_file)

    send_help_email( user=current_user, eapp=page, emsg=tb_str, etime=str(datetime.now()), session_file=session_file_name)
    flash("Your scream for help has been sent. We will get in contact with you as soon as possible.")
    return redirect(url_for(page))


