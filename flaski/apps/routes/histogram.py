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
from flaski.routines import session_to_file, check_session_app, handle_exception
from flaski.routes import FREEAPPS
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

ALLOWED_EXTENSIONS=["xlsx","tsv","csv"]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/histogram/<download>', methods=['GET', 'POST'])
@app.route('/histogram', methods=['GET', 'POST'])
@login_required
def histogram(download=None):

    apps=FREEAPPS+session["PRIVATE_APPS"]
    
    reset_info=check_session_app(session,"histogram",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."

        plot_arguments, lists, notUpdateList, checkboxes=figure_defaults()

        session["plot_arguments"]=plot_arguments
        session["lists"]=lists
        session["notUpdateList"]=notUpdateList
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="histogram"
        session["checkboxes"]=checkboxes
        
    """
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """
    if request.method == 'POST' :
        
        
        try:
            # READ SESSION FILE IF AVAILABLE
            # AND OVERWRITE VARIABLES
            inputsessionfile = request.files["inputsessionfile"]
            if inputsessionfile:
                if inputsessionfile.filename.rsplit('.', 1)[1].lower() != "ses"  :
                    plot_arguments=session["plot_arguments"]
                    error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file with the correct `ses` extension."
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)

                session_=json.load(inputsessionfile)
                if session_["ftype"]!="session":
                    plot_arguments=session["plot_arguments"]
                    error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)

                if session_["app"]!="histogram":
                    plot_arguments=session["plot_arguments"]
                    error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)
        
                del(session_["ftype"])
                del(session_["COMMIT"])
                del(session_["PRIVATE_APPS"])
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
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)

                session_=json.load(inputargumentsfile)
                if session_["ftype"]!="arguments":
                    plot_arguments=session["plot_arguments"]
                    error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)

                if session_["app"]!="histogram":
                    plot_arguments=session["plot_arguments"]
                    error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename=session["filename"], apps=apps, **plot_arguments)

                del(session_["ftype"])
                del(session_["COMMIT"])
                del(session_["PRIVATE_APPS"])
                for k in list(session_.keys()):
                    session[k]=session_[k]
                plot_arguments=session["plot_arguments"]
                flash('Arguments file sucessufuly read.',"info")
            
            # IF THE USER UPLOADS A NEW FILE
            # THEN UPDATE THE SESSION FILE
            # READ INPUT FILE
            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):
                    session["filename"]=filename
                    fileread = inputfile.read()
                    filestream=io.BytesIO(fileread)
                    extension=filename.rsplit('.', 1)[1].lower()
                    if extension == "xlsx":
                        df=pd.read_excel(filestream)
                    elif extension == "csv":
                        df=pd.read_csv(filestream)
                    elif extension == "tsv":
                        df=pd.read_csv(filestream,sep="\t")
                    
                    df=df.astype(str)
                    session["df"]=df.to_json()
                    session["plot_arguments"]["df"]=df
                    
                    cols=df.columns.tolist()


                    # IF THE USER HAS NOT YET CHOOSEN COLUMNS TO PLOT AS HISTOGRAMS
                    if "vals" not in session["plot_arguments"].keys():

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
            
            if not inputsessionfile and not inputargumentsfile:
                # SELECTION LISTS DO NOT GET UPDATED
                lists=session["lists"]

                # USER INPUT/PLOT_ARGUMENTS GETS UPDATED TO THE LATEST INPUT
                # WITH THE EXCEPTION OF SELECTION LISTS
                plot_arguments=session["plot_arguments"]
                cols=session["plot_arguments"]["df"].columns.tolist()
                
                #IN CASE THE USER HAS UNSELECTED ALL THE COLUMNS THAT WE NEED TO PLOT THE HISTOGRAMS
                if request.form.getlist("vals") == []:
                    filename=session["filename"]
                    session["plot_arguments"]["cols"]=cols
                    sometext="Please select the columns from which we will plot your histograms"
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/histogram.html' , filename=filename, apps=apps,**plot_arguments)
                    
                #IF THE USER SELECTED THE COLUMNS TO BE PLOTTED FOR THE FIRST TIME,
                #WE INITIALIZE THE DICTIONARY GROUPS SETTINGS
                if plot_arguments["groups_settings"] == dict():
                    plot_arguments["vals"]=request.form.getlist("vals")
                    groups=plot_arguments["vals"]
                    groups.sort()
                    groups_settings=dict()
                    for group in groups:
                        groups_settings[group]={"name":group,\
                            "values":plot_arguments["df"][group],\
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
                            "log_scale":"on",\
                            "fill_alpha":0.8}
                    plot_arguments["groups_settings"]=groups_settings
                    
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
                
                
                #IF THE USER HAS SELECTED NEW COLUMNS TO BE PLOTTED
                if plot_arguments["vals"]!=request.form.getlist("vals"):
                    plot_arguments["vals"]=request.form.getlist("vals")
                    groups=plot_arguments["vals"]
                    groups.sort()
                    groups_settings=dict()
                    group_dic={}
                                        
                    for group in groups:
                        if group not in plot_arguments["groups_settings"].keys():
                            groups_settings[group]={"name":group,\
                                    "values":plot_arguments["df"][group],\
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
                                    "log_scale":"on",\
                                    "fill_alpha":0.8}
                        
                        else:
                            groups_settings[group]={"name":group,\
                            "values":plot_arguments["df"][group],\
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
                        
                            #Checkboxes are only present in request form if they are checked
                            if group+".log_scale/" in list(request.form.keys()):
                                groups_settings[group]["log_scale"]=request.form["%s.log_scale/" %group]

                            else:
                                groups_settings[group]["log_scale"]="on"

                    plot_arguments["groups_settings"]=groups_settings
                
                #IF USER HAS NOT SELECTED NEW COLUMNS TO BE PLOTTED BU THEY HAVE UPDATED THE HISTOGRAM ARGUMENTS, THEN REQUEST ALL THE ARGUMENTS AGAIN
                elif plot_arguments["vals"]==request.form.getlist("vals"):
                    groups=plot_arguments["vals"]
                    groups.sort()
                    groups_settings=dict()
                    group_dic={}
                    for group in groups:
                        groups_settings[group]={"name":group,\
                        "values":plot_arguments["df"][group],\
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
                        
                        #Checkboxes are only present in request form if they are checked
                        if group+".log_scale/" in list(request.form.keys()):
                            groups_settings[group]["log_scale"]=request.form["%s.log_scale/" %group]
                        else:
                            groups_settings[group]["log_scale"]="on"
                    plot_arguments["groups_settings"]=groups_settings

                
                # # VALUES SELECTED FROM SELECTION LISTS
                # # GET UPDATED TO THE LATEST CHOICE
                
                for a in list(plot_arguments.keys()):
                    if ( a in list(request.form.keys()) ) & ( a not in list(lists.keys())+session["notUpdateList"] ):
                             plot_arguments[a]=request.form[a]

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
            

            if "df" not in list(session.keys()):
                    error_msg="No data to plot, please upload a data or session  file."
                    flash(error_msg,'error')
                    return render_template('/apps/histogram.html' , filename="Select file..", apps=apps,  **plot_arguments)
          
            
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
            
            print(plot_arguments["groups_settings"])
            return render_template('/apps/histogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="histogram",session=session)
            flash(tb_str,'traceback')
            return render_template('/apps/histogram.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":
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

            eventlog = UserLogging(email=current_user.email,action="download figure histogram")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        eventlog = UserLogging(email=current_user.email, action="visit histogram")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/histogram.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])
