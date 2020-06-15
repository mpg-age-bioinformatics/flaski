from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.pca import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file
import plotly
import plotly.io as pio
from flaski.email import send_exception_email

import os
import io
import sys
import random
import json

import pandas as pd

import base64

@app.route('/pca/<download>', methods=['GET', 'POST'])
@app.route('/pca', methods=['GET', 'POST'])
@login_required
def pca(download=None):

    apps=current_user.user_apps

    reset_info=check_session_app(session,"pca",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="pca"

    if request.method == 'POST':

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"pca")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/pca.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"pca")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/pca.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                plot_arguments=read_request(request)

                if "df" in list(session.keys()):
                    available_rows=pd.read_json(session["df"])
                    if plot_arguments["xvals"] in available_rows.columns.tolist():
                        available_rows=available_rows[plot_arguments["xvals"]].tolist()
                        available_rows=list(set(available_rows))
                        available_rows.sort()
                        plot_arguments["available_rows"]=available_rows

                # UPDATE SESSION VALUES
                session["plot_arguments"]=plot_arguments
            
            # IF THE UPLOADS A NEW FILE 
            # THAN UPDATE THE SESSION FILE
            # READ INPUT FILE
            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):
                    df=read_tables(inputfile) 
                    cols=df.columns.tolist()

                    # IF THE USER HAS NOT YET CHOOSEN X AND Y VALUES THAN PLEASE SELECT
                    if (session["plot_arguments"]["yvals"] not in cols):

                        session["plot_arguments"]["xcols"]=cols
                        session["plot_arguments"]["xvals"]=cols[0]

                        session["plot_arguments"]["ycols"]=cols
                        session["plot_arguments"]["yvals"]=cols[1:]

                        available_rows=pd.read_json(session["df"])
                        if plot_arguments["xvals"] in available_rows.columns.tolist():
                            available_rows=available_rows[plot_arguments["xvals"]].tolist()
                            available_rows=list(set(available_rows))
                            available_rows.sort()
                            session["plot_arguments"]["available_rows"]=available_rows
                                    
                        sometext="Please select which columns should be used for plotting."
                        plot_arguments=session["plot_arguments"]
                        flash(sometext,'info')
                        return render_template('/apps/pca.html' , filename=filename, apps=apps, **plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/pca.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if "df" not in list(session.keys()):
                    error_message="No data to plot, please upload a data or session  file."
                    flash(error_msg,'error')
                    return render_template('/apps/pca.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            # CALL FIGURE FUNCTION
            # try:
            df_out=make_figure(df,plot_arguments)


            return render_template('/apps/pca.html', filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="pca",session=session)
            filename=session["filename"]
            flash(tb_str,'traceback')
            return render_template('/apps/pca.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            # CALL FIGURE FUNCTION

            df_out=make_figure(df,plot_arguments)

            excelfile = io.BytesIO()
            EXC=pd.ExcelWriter(excelfile)
            df_out.to_excel(EXC,index=None)
            EXC.save()
            excelfile.seek(0)

            eventlog = UserLogging(email=current_user.email,action="download table pca values")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")
        
        return render_template('apps/pca.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])            