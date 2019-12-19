from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from app import app
from werkzeug.utils import secure_filename
from flask_session import Session
from app.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from app import db
from werkzeug.urls import url_parse
from app.plots.figures.scatterplot import make_figure, figure_defaults
from app.models import User, UserLogging


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

sess = Session()
sess.init_app(app)

ALLOWED_EXTENSIONS=["xlsx","tsv","csv"]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def landingpage():
    return redirect(url_for('login'))

@app.route('/scatterplot', methods=['GET', 'POST'])
@login_required
def scatterplot():
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       

    if request.method == 'POST':
        # READ SESSION FILE IF AVAILABLE 
        # AND OVERWRITE VARIABLES
        inputsessionfile = request.files["inputsessionfile"]
        if inputsessionfile:
            session_=json.load(inputsessionfile)
            for k in list(session_.keys()):
                session[k]=session_[k]
            plot_arguments=session["plot_arguments"]

        else:
            # SELECTION LISTS DO NOT GET UPDATED 
            lists=session["lists"]

            # USER INPUT/PLOT_ARGUMENTS GETS UPDATED TO THE LATEST INPUT
            # WITH THE EXCEPTION OF SELECTION LISTS
            plot_arguments = session["plot_arguments"]
            for a in list(plot_arguments.keys()):
                if ( a in list(request.form.keys()) ) & ( a not in list(lists.keys())+session["notUpdateList"] ):
                    plot_arguments[a]=request.form[a]

            # VALUES SELECTED FROM SELECTION LISTS 
            # GET UPDATED TO THE LATEST CHOICE
            for k in list(lists.keys()):
                if k in list(request.form.keys()):
                    plot_arguments[lists[k]]=request.form[k]

            # UPDATE SESSION VALUES
            session["plot_arguments"]=plot_arguments
        
        # IF THE CURRENT FILE IS DIFFERENT FROM 
        # THE FILE CURRENTLY IN MEMORY FOR THIS SESSION
        # THAN UPDATE THE SESSION FILE
        # READ INPUT FILE
        inputfile = request.files["inputfile"]
        if inputfile:
            filename = secure_filename(inputfile.filename)
            if allowed_file(inputfile.filename):
                session["filename"]=filename
                fileread = inputfile.read()
                extension=filename.rsplit('.', 1)[1].lower()
                if extension == "xlsx":
                    filestream=io.BytesIO(fileread)
                    df=pd.read_excel(filestream)
                elif extension == "csv":
                    df=pd.read_csv(fileread)
                elif extension == "tsv":
                    df=pd.read_csv(fileread,sep="\t")
                
                session["df"]=df.to_json()
                
                cols=df.columns.tolist()

                # IF THE USER HAS NOT YET CHOOSEN X AND Y VALUES THAN PLEASE SELECT
                if (session["plot_arguments"]["xvals"] not in cols) & (session["plot_arguments"]["yvals"] not in cols):

                    session["plot_arguments"]["xcols"]=cols
                    session["plot_arguments"]["xvals"]=cols[0]

                    session["plot_arguments"]["ycols"]=cols
                    session["plot_arguments"]["yvals"]=cols[1]
                
                    sometext="Please select which values should map to the x and y axes."
                    plot_arguments=session["plot_arguments"]
                    return render_template('plots/scatterplot.html' , filename=filename, sometext=sometext, **plot_arguments)
                
            else:
                # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                has the correct format and respective extension and try uploadling it again." %filename
                return render_template('/plots/scatterplot.html' , filename="Select file..", error_message=error_message, **plot_arguments)
        
        # READ INPUT DATA FROM SESSION JSON
        df=pd.read_json(session["df"])

        # CALL FIGURE FUNCTION
        fig=make_figure(df,plot_arguments)

        # TRANSFORM FIGURE TO BYTES AND BASE64 STRING
        figfile = io.BytesIO()
        plt.savefig(figfile, format='png')
        plt.close()
        figfile.seek(0)  # rewind to beginning of file
        figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

        # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
        filename=session["filename"]
        plot_arguments=session["plot_arguments"]
        return render_template('plots/scatterplot.html', figure_url=figure_url, filename=filename, **plot_arguments)

    else:
        #sometext="get"

        # INITIATE SESSION
        session["filename"]="Select file.."

        plot_arguments, lists, notUpdateList=figure_defaults()

        session["plot_arguments"]=plot_arguments
        session["lists"]=lists
        session["notUpdateList"]=notUpdateList
        session["COMMIT"]=app.config['COMMIT']

        eventlog = UserLogging(email=current_user.email,action="visit scatterplot")
        db.session.add(eventlog)
        db.session.commit()

        return render_template('plots/scatterplot.html',  filename=session["filename"], **plot_arguments)

@app.route('/figure', methods=['GET','POST'])
@login_required
def figure():
    # READ INPUT DATA FROM SESSION JSON
    df=pd.read_json(session["df"])

    plot_arguments=session["plot_arguments"]

    # CALL FIGURE FUNCTION
    fig=make_figure(df,plot_arguments)

    #flash('Figure is being sent to download but will not be updated on your screen.')
    figfile = io.BytesIO()
    mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
    plt.savefig(figfile, format=plot_arguments["downloadf"])
    plt.close()
    figfile.seek(0)  # rewind to beginning of file

    eventlog = UserLogging(email=current_user.email,action="download figure scatterplot")
    db.session.add(eventlog)
    db.session.commit()

    return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

@app.route('/downloadarguments', methods=['GET','POST'])
@login_required
def downloadarguments():
    # READ INPUT DATA FROM SESSION JSON
    session_={}
    for k in list(session.keys()):
        if k not in ['_permanent','fileread','_flashes',"width","height","df"]:
            session_[k]=session[k]

    session_file = io.BytesIO()
    session_file.write(json.dumps(session_).encode())
    session_file.seek(0)

    plot_arguments=session["plot_arguments"]

    eventlog = UserLogging(email=current_user.email,action="download arguments scatterplot")
    db.session.add(eventlog)
    db.session.commit()

    return send_file(session_file, mimetype='application/json', as_attachment=True, attachment_filename=plot_arguments["session_argumentsn"]+".json" )

@app.route('/downloadsession', methods=['GET','POST'])
@login_required
def downloadsession():
    # READ INPUT DATA FROM SESSION JSON
    session_={}
    for k in list(session.keys()):
        if k not in ['_permanent','fileread','_flashes',"width","height"]:
            session_[k]=session[k]

    session_file = io.BytesIO()
    session_file.write(json.dumps(session_).encode())
    session_file.seek(0)

    plot_arguments=session["plot_arguments"]

    eventlog = UserLogging(email=current_user.email,action="download session scatterplot")
    db.session.add(eventlog)
    db.session.commit()

    return send_file(session_file, mimetype='application/json', as_attachment=True, attachment_filename=plot_arguments["session_downloadn"]+".json" )