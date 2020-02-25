from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.iheatmap import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routes import FREEAPPS
import plotly
import plotly.io as pio



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

import pandas as pd

import base64

ALLOWED_EXTENSIONS=["xlsx","tsv","csv"]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/iheatmap/<download>', methods=['GET', 'POST'])
@app.route('/iheatmap', methods=['GET', 'POST'])
@login_required
def iheatmap(download=None):
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
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)

            session_=json.load(inputsessionfile)
            if session_["ftype"]!="session":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)

            if session_["app"]!="iheatmap":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)
    
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
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)

            session_=json.load(inputargumentsfile)
            if session_["ftype"]!="arguments":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)

            if session_["app"]!="iheatmap":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)

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
                    if a == "yvals":
                        plot_arguments[a]=request.form.getlist(a)
                    else:
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
                        if (plot_arguments[checkbox][0]!="."):
                            plot_arguments[checkbox]="off"

            # UPDATE SESSION VALUES
            session["plot_arguments"]=plot_arguments
        
        # IF THE UPLOADS A NEW FILE 
        # THAN UPDATE THE SESSION FILE
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
                    df=pd.read_excel(filestream, index_col=False)
                elif extension == "csv":
                    df=pd.read_csv(filestream, index_col=False)
                elif extension == "tsv":
                    df=pd.read_csv(filestream,sep="\t", index_col=False)
                
                session["df"]=df.to_json()
                
                cols=df.columns.tolist()

                # if session["plot_arguments"]["yvals_colors"] not in cols:
                #     session["plot_arguments"]["yvals_colors"]=["None"]+cols

                # if session["plot_arguments"]["xvals_colors"] not in df[cols[0]].tolist():
                #     session["plot_arguments"]["xvals_colors"]=["select a row.."]+df[cols[0]].tolist()


                # IF THE USER HAS NOT YET CHOOSEN X AND Y VALUES THAN PLEASE SELECT
                if (session["plot_arguments"]["yvals"] not in cols):

                    session["plot_arguments"]["xcols"]=cols
                    session["plot_arguments"]["xvals"]=cols[0]

                    session["plot_arguments"]["ycols"]=cols
                    session["plot_arguments"]["yvals"]=cols[1:]
                                  
                    sometext="Please select which columns should be used for plotting."
                    plot_arguments=session["plot_arguments"]
                    flash(sometext,'info')
                    return render_template('/apps/iheatmap.html' , filename=filename, apps=apps, **plot_arguments)
                
            else:
                # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                has the correct format and respective extension and try uploadling it again." %filename
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename="Select file..", apps=apps, **plot_arguments)
        
        if "df" not in list(session.keys()):
                error_message="No data to plot, please upload a data or session  file."
                flash(error_msg,'error')
                return render_template('/apps/iheatmap.html' , filename="Select file..", apps=apps,  **plot_arguments)
 
        #if session["plot_arguments"]["groups_value"]=="None":
        #    session["plot_arguments"]["groups_auto_generate"]=".on"

        # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
        filename=session["filename"]
        plot_arguments=session["plot_arguments"]

        # READ INPUT DATA FROM SESSION JSON
        df=pd.read_json(session["df"])

        # CALL FIGURE FUNCTION
        try:
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            return render_template('/apps/iheatmap.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            flash(e,'error')

            return render_template('/apps/iheatmap.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            pio.orca.config.executable='/miniconda/bin/orca'
            pio.orca.config.use_xvfb = True
            #pio.orca.config.save()
            #flash('Figure is being sent to download but will not be updated on your screen.')
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            fig.write_image(figfile, format=plot_arguments["downloadf"], height=float(plot_arguments["fig_height"]) , width=float(plot_arguments["fig_width"]))
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure heatmap")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        if download == "clusters":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION

            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            excelfile = io.BytesIO()
            EXC=pd.ExcelWriter(excelfile)
            df_.to_excel(EXC,sheet_name="heatmap",index=None)
            cols_cluster_numbers.to_excel(EXC,sheet_name="rows",index=None)
            index_cluster_numbers.to_excel(EXC,sheet_name="cols",index=None)
            EXC.save()
            excelfile.seek(0)

            eventlog = UserLogging(email=current_user.email,action="download figure heatmap clusters")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")

        if "app" not in list(session.keys()):
            return_to_plot=False
        elif session["app"] != "iheatmap" :
            return_to_plot=False
        else:
            return_to_plot=True

        if not return_to_plot:
            # INITIATE SESSION
            session["filename"]="Select file.."

            plot_arguments, lists, notUpdateList, checkboxes=figure_defaults()

            session["plot_arguments"]=plot_arguments
            session["lists"]=lists
            session["notUpdateList"]=notUpdateList
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="iheatmap"
            session["checkboxes"]=checkboxes

        eventlog = UserLogging(email=current_user.email, action="visit iheatmap")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/iheatmap.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])