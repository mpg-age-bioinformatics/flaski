from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.histogram import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routines import session_to_file
from flaski.routes import FREEAPPS

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

import pandas as pd

import base64

@app.route('/histogram/<download>', methods=['GET', 'POST'])
@app.route('/histogram', methods=['GET', 'POST'])
@login_required
def histogram(download=None):
    """
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """

    apps=FREEAPPS+session["PRIVATE_APPS"]

    if request.method == 'POST':

        # READ SESSION FILE IF AVAILABLE
        # AND OVERWRITE VARIABLES
        inputsessionfile = request.files["inputsessionfile"]
        if inputsessionfile:
            if inputsessionfile.filename.rsplit('.', 1)[1].lower() != "ses"  :
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file with the correct `ses` extension."
                flash(error_msg,'error')
                return render_template('/apps/histogram.html', apps=apps, **plot_arguments)

            session_=json.load(inputsessionfile)
            if session_["ftype"]!="session":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , apps=apps, **plot_arguments)

            if session_["app"]!="histogram":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , apps=apps, **plot_arguments)
    
            del(session_["ftype"])
            del(session_["COMMIT"])
            for k in list(session_.keys()):
                session[k]=session_[k]
            plot_arguments=session["plot_arguments"]
            flash('Session file sucessufuly read.')


        # READ ARGUMENTS FILE IF AVAILABLE
        # AND OVERWRITE VARIABLES
        inputargumentsfile = request.files["inputargumentsfile"]
        if inputargumentsfile :
            if inputargumentsfile.filename.rsplit('.', 1)[1].lower() != "arg"  :
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a arguments file. Please make sure you upload a session file with the correct `arg` extension."
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , apps=apps, **plot_arguments)

            session_=json.load(inputargumentsfile)
            if session_["ftype"]!="arguments":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , apps=apps, **plot_arguments)

            if session_["app"]!="histogram":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , apps=apps, **plot_arguments)

            del(session_["ftype"])
            del(session_["COMMIT"])
            for k in list(session_.keys()):
                session[k]=session_[k]
            plot_arguments=session["plot_arguments"]
            flash('Arguments file sucessufuly read.',"info")

        if not inputsessionfile and not inputargumentsfile:
            # SELECTION LISTS DO NOT GET UPDATED
            lists=session["lists"]

            # USER INPUT/PLOT_ARGUMENTS GETS UPDATED TO THE LATEST INPUT
            # WITH THE EXCEPTION OF SELECTION LISTS
            plot_arguments = session["plot_arguments"]
            for a in list(plot_arguments.keys()):
                if ( a in list(request.form.keys()) ) & ( a not in list(lists.keys())+session["notUpdateList"] ):
                    plot_arguments[a]=request.form[a]

            # # VALUES SELECTED FROM SELECTION LISTS
            # # GET UPDATED TO THE LATEST CHOICE
            # for k in list(lists.keys()):
            #     if k in list(request.form.keys()):
            #         plot_arguments[lists[k]]=request.form[k]
            # checkboxes
            for checkbox in session["checkboxes"]:
                if checkbox in list(request.form.keys()) :
                    plot_arguments[checkbox]="on"
                else:
                    try:
                        plot_arguments[checkbox]=request.form[checkbox]
                    except:
                        if plot_arguments[checkbox][0]!=".":
                            plot_arguments[checkbox]="off"

            # UPDATE SESSION VALUES
            session["plot_arguments"]=plot_arguments
        

        # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
        plot_arguments=session["plot_arguments"]

        # CALL FIGURE FUNCTION
        try:
            fig =make_figure(plot_arguments)

            # TRANSFORM FIGURE TO BYTES AND BASE64 STRING
            figfile = io.BytesIO()
            plt.savefig(figfile, format='png')
            plt.close()
            figfile.seek(0)  # rewind to beginning of file
            figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

            return render_template('/apps/histogram.html', figure_url=figure_url,apps=apps, **plot_arguments)

        except Exception as e:
            flash(e,'error')

            return render_template('/apps/histogram.html', apps=apps, **plot_arguments)

    else:
        if download == "download":

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig =make_figure(plot_arguments)

            #flash('Figure is being sent to download but will not be updated on your screen.')
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            plt.savefig(figfile, format=plot_arguments["downloadf"])
            plt.close()
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure histogram")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        if download == "data":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            # CALL FIGURE FUNCTION

            fig =make_figure(plot_arguments)

            excelfile = io.BytesIO()
            EXC=pd.ExcelWriter(excelfile)
            #df.to_excel(EXC,sheet_name="histogram",index=None)
            EXC.save()
            excelfile.seek(0)

            eventlog = UserLogging(email=current_user.email,action="download figure histogram data")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")



        if "app" not in list(session.keys()):
            return_to_plot=False
        elif session["app"] != "histogram" :
            return_to_plot=False
        else:
            return_to_plot=True

        if not return_to_plot:
            # INITIATE SESSION

            plot_arguments, lists, notUpdateList, checkboxes=figure_defaults()

            session["plot_arguments"]=plot_arguments
            session["lists"]=lists
            session["notUpdateList"]=notUpdateList
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="histogram"
            session["checkboxes"]=checkboxes

        eventlog = UserLogging(email=current_user.email, action="visit histogram")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/histogram.html', apps=apps, **session["plot_arguments"])

