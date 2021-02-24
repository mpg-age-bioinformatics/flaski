from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.submission import submission_check #, submission_defaults
from flaski.models import User, UserLogging
from flaski.email import send_exception_email
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file


import os
import io
import sys
import random
import json

import pandas as pd
import numpy as np

import base64

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

@app.route('/submissions', methods=['GET', 'POST'])
@login_required
def submissions():

    apps=current_user.user_apps

    reset_info=check_session_app(session,"submissions",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."

        # submission_arguments=submission_defaults()

        # session["plot_arguments"]=submission_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="submissions"

    if request.method == 'POST' :

        try:
            # if request.files["inputsessionfile"] :
            #     msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"submissions")
            #     if error:
            #         flash(msg,'error')
            #         return render_template('/apps/submissions.html' , filename=session["filename"],apps=apps, **plot_arguments)
            #     flash(msg,"info")

            # if request.files["inputargumentsfile"] :
            #     msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"david")
            #     if error:
            #         flash(msg,'error')
            #         return render_template('/apps/submissions.html' , filename=session["filename"], apps=apps, **plot_arguments)
            #     flash(msg,"info")

            # if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
            plot_arguments=read_request(request)

            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):
                    df=read_tables(inputfile)

            # CALL FIGURE FUNCTION
            status, msg=submission_check(df)
            if not status:
                flash(msg,"error")
                return render_template('/apps/submissions.html', apps=apps) #, **plot_arguments)

            if status:
                flash(msg)
                return render_template('/apps/submissions.html', apps=apps) #, **plot_arguments)


            # return render_template('/apps/submissions.html', apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="submissions",session=session)
            flash(tb_str,'traceback')
            return render_template('/apps/submissions.html', apps=apps) #, **plot_arguments)

    else:

        return render_template('apps/submissions.html',  apps=apps) #, **session["plot_arguments"])
