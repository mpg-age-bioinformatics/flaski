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
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file, separate_apps
from flaski.email import send_exception_email


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

@app.route('/histogram/<download>', methods=['GET', 'POST'])
@app.route('/histogram', methods=['GET', 'POST'])
@login_required
def histogram(download=None):

    apps=current_user.user_apps
    plot_arguments=None  

    reset_info=check_session_app(session,"histogram",apps)
    submissions, apps=separate_apps(current_user.user_apps)

    
    if reset_info:

        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="histogram"
        
    """
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """
    if request.method == 'POST' :
        
        try:
            if request.files["inputsessionfile"] :
                msg,plot_arguments,error=read_session_file(request.files["inputsessionfile"],"histogram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"histogram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")
            
            # IF THE USER UPLOADS A NEW FILE
            # THEN UPDATE THE SESSION FILE
            # READ INPUT FILE
            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):

                    df=read_tables(inputfile)
                    cols=df.columns.tolist()
                    
                    # INDICATE THE USER TO SELECT THE COLUMNS TO PLOT AS HISTOGRAMS
                    session["plot_arguments"]=figure_defaults()
                    session["plot_arguments"]["cols"]=cols

                    sometext="Please select the columns from which we will plot your histograms"
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/histogram.html' , filename=filename, apps=apps,**plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename="Select file..", apps=apps, **plot_arguments)

            if "df" not in list(session.keys()):
                error_msg="No data to plot, please upload a data or session  file."
                flash(error_msg,'error')
                return render_template('/apps/histogram.html' , filename="Select file..", apps=apps,  **plot_arguments)
            
            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :

                df=pd.read_json(session["df"])
                cols=df.columns.tolist()
                filename=session["filename"]

                #IN CASE THE USER HAS UNSELECTED ALL THE COLUMNS THAT WE NEED TO PLOT THE HISTOGRAMS
                if request.form.getlist("vals") == []:
                    filename=session["filename"]
                    session["plot_arguments"]=figure_defaults()
                    session["plot_arguments"]["cols"]=cols
                    sometext="Please select the columns from which we will plot your histograms"
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/histogram.html' , filename=filename, apps=apps,**plot_arguments)
                    
                #IF THE USER SELECTED THE COLUMNS TO BE PLOTTED FOR THE FIRST TIME,
                #WE INITIALIZE THE DICTIONARY GROUPS SETTINGS
                plot_arguments=session["plot_arguments"]
                if plot_arguments["groups_settings"] == dict():
                    plot_arguments["vals"]=request.form.getlist("vals")
                    groups=plot_arguments["vals"]
                    groups.sort()
                    groups_settings=dict()
                    for group in groups:
                        groups_settings[group]={"name":group,\
                            "values":df[group].tolist(),\
                            "label":group,\
                            "color_value":None,\
                            "color_rgb":"",\
                            "bins_value":"auto",\
                            "bins_number":"",\
                            "orientation_value":"vertical",\
                            "histtype_value":"bar",\
                            "linewidth":0.5,\
                            "linestyle_value":"solid",\
                            "line_color":None,\
                            "line_rgb":"",\
                            "fill_alpha":0.8,\
                            "density":".off",\
                            "cumulative":".off"}
                            
                    plot_arguments["groups_settings"]=groups_settings
                    plot_arguments=read_request(request)
                    
                    #CALL FIGURE FUNCTION
                    fig=make_figure(df,plot_arguments)
                    #TRANSFORM FIGURE TO BYTES AND BASE64 STRING
                    figfile = io.BytesIO()
                    plt.savefig(figfile, format='png')
                    plt.close()
                    figfile.seek(0)  # rewind to beginning of file
                    figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')
                    return render_template('/apps/histogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)
                
                
                #IF THE USER HAS SELECTED NEW COLUMNS TO BE PLOTTED
                # if plot_arguments["vals"]!=request.form.getlist("vals"):
                
                #groups=plot_arguments["vals"]
                groups=request.form.getlist("vals")
                groups.sort()
                groups_settings=dict()
                                    
                for group in groups:
                    if group not in list(plot_arguments["groups_settings"].keys()):
                        groups_settings[group]={"name":group,\
                                "label":group,\
                                "color_value":None,\
                                "color_rgb":"",\
                                "bins_value":"auto",\
                                "bins_number":"",\
                                "orientation_value":"vertical",\
                                "histtype_value":"bar",\
                                "linewidth":0.5,\
                                "linestyle_value":"solid",\
                                "line_color":None,\
                                "line_rgb":"",\
                                "fill_alpha":0.8,
                                "density":".off",\
                                "cumulative":".off"}
                    
                    else:
                        groups_settings[group]={"name":group,\
                        "label":request.form["%s.label" %group],\
                        "color_value":request.form["%s.color_value" %group],\
                        "color_rgb":request.form["%s.color_rgb" %group],\
                        "bins_value":request.form["%s.bins_value" %group],\
                        "bins_number":request.form["%s.bins_number" %group],\
                        "orientation_value":request.form["%s.orientation_value" %group],\
                        "histtype_value":request.form["%s.histtype_value" %group],\
                        "linewidth":request.form["%s.linewidth" %group],\
                        "linestyle_value":request.form["%s.linestyle_value" %group],\
                        "line_color":request.form["%s.line_color" %group],\
                        "line_rgb":request.form["%s.line_rgb" %group],\
                        "fill_alpha":request.form["%s.fill_alpha" %group]}
                        
                        #If the user does not tick the options the arguments do not appear as keys in request.form
                        if "%s.density"%group in request.form.keys():
                            groups_settings[group]["density"]="on" #request.form["%s.density" %group]
                        else:
                            groups_settings[group]["density"]="off"
                        
                        if "%s.cumulative"%group in request.form.keys():
                            groups_settings[group]["cumulative"]="on" #request.form["%s.cumulative" %group]
                        else:
                            groups_settings[group]["cumulative"]="off"

                plot_arguments["groups_settings"]=groups_settings

                plot_arguments=read_request(request)
                #session["plot_arguments"]=plot_arguments           

          
            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]
         
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            #CALL FIGURE FUNCTION
            # try:
            fig=make_figure(df,plot_arguments)

            #TRANSFORM FIGURE TO BYTES AND BASE64 STRING
            figfile = io.BytesIO()
            plt.savefig(figfile, format='png')
            plt.close()
            figfile.seek(0)  # rewind to beginning of file
            figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')
            
            return render_template('/apps/histogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="histogram",session=session)
            flash(tb_str,'traceback')
            if not plot_arguments:
                plot_arguments=session["plot_arguments"]
            return render_template('/apps/histogram.html', filename=session["filename"], apps=apps, **session["plot_arguments"])

    else:

        if download == "download":

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig=make_figure(df,plot_arguments)

            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            plt.savefig(figfile, format=plot_arguments["downloadf"])
            plt.close()
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure histogram")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )
            
        return render_template('apps/histogram.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])