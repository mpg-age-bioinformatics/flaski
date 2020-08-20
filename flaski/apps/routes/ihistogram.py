from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.ihistogram import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file
from flaski.email import send_exception_email
import plotly
import plotly.io as pio

import os
import io
import sys
import random
import json

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

@app.route('/ihistogram/<download>', methods=['GET', 'POST'])
@app.route('/ihistogram', methods=['GET', 'POST'])
@login_required
def ihistogram(download=None):

    apps=current_user.user_apps
    reset_info=check_session_app(session,"ihistogram",apps)
    
    if reset_info:

        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="ihistogram"
        
    """
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """
    if request.method == 'POST' :
        
        try:
            if request.files["inputsessionfile"] :
                msg,plot_arguments,error=read_session_file(request.files["inputsessionfile"],"ihistogram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/ihistogram.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"ihistogram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/ihistogram.html' , filename=session["filename"], apps=apps, **plot_arguments)
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

                    sometext="Please select the columns from which we will plot your iHistograms"
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/ihistogram.html' , filename=filename, apps=apps,**plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/ihistogram.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :

                df=pd.read_json(session["df"])
                cols=df.columns.tolist()
                filename=session["filename"]

                #IN CASE THE USER HAS UNSELECTED ALL THE COLUMNS THAT WE NEED TO PLOT THE HISTOGRAMS
                if request.form.getlist("vals") == []:
                    session["plot_arguments"]=figure_defaults()
                    session["plot_arguments"]["cols"]=cols
                    sometext="Please select the columns from which we will plot your iHistograms"
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/ihistogram.html' , filename=filename, apps=apps,**plot_arguments)
                    
                #IF THE USER SELECTED THE COLUMNS TO BE PLOTTED FOR THE FIRST TIME OR IF THE USER CHANGES FROM KDE TO HIST OR FROM HIST TO KDE
                if "kde" in request.form.keys() and session["plot_arguments"]["kde"]=="on":
                    kde=False
                elif "kde" not in request.form.keys() and session["plot_arguments"]["kde"] in [".off","off"]:
                    kde=False
                else:
                    kde=True
                
                if session["plot_arguments"]["groups_settings"] == dict() or kde or session["plot_arguments"]["vals"]!=request.form.getlist("vals"):
                    if "kde" not in request.form.keys():
                        plot_arguments=session["plot_arguments"]
                        plot_arguments["vals"]=request.form.getlist("vals")
                        groups=plot_arguments["vals"]
                        groups.sort()
                        groups_settings=dict()
                        for group in groups:
                            groups_settings[group]={"name":group,\
                                "values":df[group],\
                                "label":group,\
                                "color_value":"None",\
                                "color_rgb":"",\
                                "histnorm":"",\
                                "orientation_value":"vertical",\
                                "linewidth":0.5,\
                                "linestyle_value":"solid",\
                                "line_color":"lightgrey",\
                                "line_rgb":"",\
                                "opacity":"0.8",\
                                "text":"",\
                                "bins_number":"",\
                                "hoverinfo":"all",\
                                "hover_bgcolor":"None",\
                                "hover_bordercolor":"None",\
                                "hover_align":"auto",\
                                "hover_fontfamily":"Default",\
                                "hover_fontsize":"12",\
                                "hover_fontcolor":"None",\
                                "histfunc":"count",\
                                "density":".off",\
                                "cumulative_direction":"increasing",\
                                "cumulative":".off"}
                        
                        #plot_arguments=read_request(request)       
                        plot_arguments["groups_settings"]=groups_settings
                        session["plot_arguments"]=plot_arguments
                        filename=session["filename"]
                        plot_arguments=session["plot_arguments"]
            
                        # READ INPUT DATA FROM SESSION JSON
                        df=pd.read_json(session["df"])
                        #CALL FIGURE FUNCTION
                        fig=make_figure(df,plot_arguments)
                        figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                        return render_template('/apps/ihistogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

                    else:
                        plot_arguments=session["plot_arguments"]
                        plot_arguments["vals"]=request.form.getlist("vals")
                        groups=plot_arguments["vals"]
                        groups.sort()
                        groups_settings=dict()
                        for group in groups:
                            groups_settings[group]={
                                "label":group,\
                                "color_value":"None",\
                                "color_rgb":"",\
                                }
                        plot_arguments=read_request(request)
                        plot_arguments["groups_settings"]=groups_settings
                        session["plot_arguments"]=plot_arguments
                        filename=session["filename"]
                        plot_arguments=session["plot_arguments"]
            
                        # READ INPUT DATA FROM SESSION JSON
                        df=pd.read_json(session["df"])

                        #CALL FIGURE FUNCTION
                        fig=make_figure(df,plot_arguments)
                        figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

                        return render_template('/apps/ihistogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

            if "df" not in list(session.keys()):
                error_msg="No data to plot, please upload a data or session  file."
                flash(error_msg,'error')
                return render_template('/apps/ihistogram.html' , filename="Select file..", apps=apps,  **plot_arguments)

          
            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            plot_arguments=read_request(request)

            # UPDATE VALUES FROM GROUPS_SETTINGS WHICH DO NOT GET UPDATED WITH THE READ_REQUEST FUNCTION
            #plot_arguments=session["plot_arguments"]
            groups=request.form.getlist("vals")
            groups_settings=dict()
            groups.sort()
            #IF THE USER WANTS TO PLOT A REGULAR HISTOGRAM  
            if plot_arguments["kde"]!="on":

                #FOR COLUMNS ALREADY SELECTED BY USER
                for group in groups:
                    if group not in plot_arguments["groups_settings"].keys():          
                        groups_settings[group]={"name":group,\
                            "label":request.form["%s.label" %group],\
                            "color_value":request.form["%s.color_value" %group],\
                            "color_rgb":request.form["%s.color_rgb" %group],\
                            "histnorm":request.form["%s.histnorm" %group],\
                            "orientation_value":request.form["%s.orientation_value" %group],\
                            "linewidth":request.form["%s.linewidth" %group],\
                            "linestyle_value":request.form["%s.linestyle_value" %group],\
                            "line_color":request.form["%s.line_color" %group],\
                            "line_rgb":request.form["%s.line_rgb" %group],\
                            "opacity":request.form["%s.opacity" %group],\
                            "text":request.form["%s.text" %group],\
                            "bins_number":request.form["%s.bins_number" %group],\
                            "hoverinfo":request.form["%s.hoverinfo" %group],\
                            "hover_bgcolor":request.form["%s.hover_bgcolor" %group],\
                            "hover_bordercolor":request.form["%s.hover_bordercolor" %group],\
                            "hover_align":request.form["%s.hover_align" %group],\
                            "hover_fontsize":request.form["%s.hover_fontsize" %group],\
                            "hover_fontcolor":request.form["%s.hover_fontcolor" %group],\
                            "hover_fontfamily":request.form["%s.hover_fontfamily" %group],\
                            "cumulative_direction":request.form["%s.cumulative_direction" %group],\
                            "histfunc":request.form["%s.histfunc" %group]
                            }
                                    
                            #If the user does not tick the options the arguments do not appear as keys in request.form
                        if "%s.density"%group in request.form.keys():
                            groups_settings[group]["density"]=request.form["%s.density" %group]
                        else:
                            groups_settings[group]["density"]="off"
                                    
                        if "%s.cumulative"%group in request.form.keys():
                            groups_settings[group]["cumulative"]=request.form["%s.cumulative" %group]
                        else:
                            groups_settings[group]["cumulative"]="off"
                    
                    #NEW COLUMNS SELECTED BY USER
                    else:
                        groups_settings[group]={"name":group,\
                            "label":request.form["%s.label" %group],\
                            "color_value":request.form["%s.color_value" %group],\
                            "color_rgb":request.form["%s.color_rgb" %group],\
                            "histnorm":request.form["%s.histnorm" %group],\
                            "orientation_value":request.form["%s.orientation_value" %group],\
                            "linewidth":request.form["%s.linewidth" %group],\
                            "linestyle_value":request.form["%s.linestyle_value" %group],\
                            "line_color":request.form["%s.line_color" %group],\
                            "line_rgb":request.form["%s.line_rgb" %group],\
                            "opacity":request.form["%s.opacity" %group],\
                            "text":request.form["%s.text" %group],\
                            "bins_number":request.form["%s.bins_number" %group],\
                            "hoverinfo":request.form["%s.hoverinfo" %group],\
                            "hover_bgcolor":request.form["%s.hover_bgcolor" %group],\
                            "hover_bordercolor":request.form["%s.hover_bordercolor" %group],\
                            "hover_align":request.form["%s.hover_align" %group],\
                            "hover_fontsize":request.form["%s.hover_fontsize" %group],\
                            "hover_fontcolor":request.form["%s.hover_fontcolor" %group],\
                            "hover_fontfamily":request.form["%s.hover_fontfamily" %group],\
                            "cumulative_direction":request.form["%s.cumulative_direction" %group],\
                            "histfunc":request.form["%s.histfunc" %group]}
                            
                        #If the user does not tick the options the arguments do not appear as keys in request.form
                        if "%s.density"%group in request.form.keys():
                            groups_settings[group]["density"]=request.form["%s.density" %group]
                        else:
                            groups_settings[group]["density"]="off"
                            
                        if "%s.cumulative"%group in request.form.keys():
                            groups_settings[group]["cumulative"]=request.form["%s.cumulative" %group]
                        else:
                            groups_settings[group]["cumulative"]="off"
            
            #IF THE USER WANTS TO PLOT A KDE PLOT
            else:
                plot_arguments=session["plot_arguments"]
                plot_arguments["vals"]=request.form.getlist("vals")
                groups=plot_arguments["vals"]
                groups.sort()
                groups_settings=dict()
                for group in groups:
                    #FOR COLUMNS NEW COLUMNS SELECTED BY USER
                    if group not in plot_arguments["groups_settings"].keys():
                        for group in groups:
                            groups_settings[group]={"label":group,\
                                    "color_value":"None",\
                                    "color_rgb":""}
                    
                    #FOR COLUMNS ALREADY SELECTED BY USER
                    else:
                        groups_settings[group]={"label":group,\
                            "color_value":request.form["%s.color_value" %group],\
                            "color_rgb":request.form["%s.color_rgb" %group]}
                    
            plot_arguments["groups_settings"]=groups_settings
            session["plot_arguments"]=plot_arguments
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            #CALL FIGURE FUNCTION
            fig=make_figure(df,plot_arguments)
            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            return render_template('/apps/ihistogram.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
                tb_str=handle_exception(e,user=current_user,eapp="ihistogram",session=session)
                flash(tb_str,'traceback')
                return render_template('/apps/ihistogram.html', filename=session["filename"], apps=apps, **session["plot_arguments"])

    else:

        if download == "download":

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig=make_figure(df,plot_arguments)

            pio.orca.config.executable='/miniconda/bin/orca'
            pio.orca.config.use_xvfb = True
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}

            pa_={}
            for v in ["fig_height","fig_width"]:
                if plot_arguments[v] != "":
                    pa_[v]=False
                elif plot_arguments[v]:
                    pa_[v]=float(plot_arguments[v])
                else:
                    pa_[v]=False

            if (pa_["fig_height"]) & (pa_["fig_width"]):
                fig.write_image( figfile, format=plot_arguments["downloadf"], height=pa_["fig_height"] , width=pa_["fig_width"] )
            else:
                fig.write_image( figfile, format=plot_arguments["downloadf"] )

            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure ihistogram")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        return render_template('apps/ihistogram.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])