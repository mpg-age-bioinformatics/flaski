from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.heatmap import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.email import send_exception_email
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file


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

import sys

@app.route('/heatmap/<download>', methods=['GET', 'POST'])
@app.route('/heatmap', methods=['GET', 'POST'])
@login_required
def heatmap(download=None):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       

    apps=current_user.user_apps

    reset_info=check_session_app(session,"heatmap",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."

        plot_arguments=figure_defaults()

        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="heatmap"

    if request.method == 'POST':

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"heatmap")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/heatmap.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"heatmap")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/heatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                plot_arguments=read_request(request)

            
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
                    if (session["plot_arguments"]["yvals"] not in cols) | (session["plot_arguments"]["xvals"] not in cols):

                        session["plot_arguments"]["xcols"]=cols
                        session["plot_arguments"]["xvals"]=cols[0]

                        session["plot_arguments"]["xvals_colors_list"]=["select a row.."]+df[session["plot_arguments"]["xvals"]].tolist()

                        session["plot_arguments"]["ycols"]=cols
                        session["plot_arguments"]["yvals"]=cols[1:]
                                    
                        sometext="Please select which columns should be used for plotting."
                        plot_arguments=session["plot_arguments"]
                        flash(sometext,'info')
                        return render_template('/apps/heatmap.html' , filename=filename, apps=apps,**plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/heatmap.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if "df" not in list(session.keys()):
                    error_message="No data to plot, please upload a data or session  file."
                    flash(error_msg,'error')
                    return render_template('/apps/heatmap.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            session["plot_arguments"]["xvals_colors_list"]=["select a row.."]+df[request.form["xvals"]].tolist()
            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            # TRANSFORM FIGURE TO BYTES AND BASE64 STRING
            figfile = io.BytesIO()
            plt.savefig(figfile, format='png')
            plt.close()
            figfile.seek(0)  # rewind to beginning of file
            figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

            return render_template('/apps/heatmap.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="heatmap",session=session)
            flash(tb_str,'traceback')
            return render_template('/apps/heatmap.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            plt.savefig(figfile, format=plot_arguments["downloadf"])
            plt.close()
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure heatmap")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        if download == "clusters":

            plot_arguments=session["plot_arguments"]
            if int(plot_arguments["n_cols_cluster"]) == 0:
                fixed_cols=True
                plot_arguments["n_cols_cluster"]=1
            else:
                fixed_cols=False

            if int(plot_arguments["n_rows_cluster"]) == 0:
                fixed_rows=True
                plot_arguments["n_rows_cluster"]=1
            else:
                fixed_rows=False

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
           
            if fixed_rows:
                plot_arguments["n_rows_cluster"]=0

            if fixed_cols:
                plot_arguments["n_cols_cluster"]=0

            eventlog = UserLogging(email=current_user.email,action="download figure heatmap clusters")
            db.session.add(eventlog)
            db.session.commit()
            
            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")
        
        return render_template('apps/heatmap.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])