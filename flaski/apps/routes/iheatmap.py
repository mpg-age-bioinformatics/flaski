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

@app.route('/iheatmap/<download>', methods=['GET', 'POST'])
@app.route('/iheatmap', methods=['GET', 'POST'])
@login_required
def iheatmap(download=None):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       

    apps=current_user.user_apps
    plot_arguments=None  

    reset_info=check_session_app(session,"iheatmap",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="iheatmap"

    if request.method == 'POST':

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"iheatmap")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/iheatmap.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"iheatmap")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/iheatmap.html' , filename=session["filename"], apps=apps, **plot_arguments)
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
                        return render_template('/apps/iheatmap.html' , filename=filename, apps=apps, **plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/iheatmap.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if "df" not in list(session.keys()):
                    error_msg="No data to plot, please upload a data or session  file."
                    flash(error_msg,'error')
                    return render_template('/apps/iheatmap.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            if len(df) == 1:
                session["plot_arguments"]["row_cluster"]="off"
                flash("You only have one row. Row dendrogram is now off.")
            if len(session["plot_arguments"]["yvals"]) == 1:
                session["plot_arguments"]["col_cluster"]="off"
                flash("You only have one column. Columns dendrogram is now off.")

            # CALL FIGURE FUNCTION
            # try:
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            return render_template('/apps/iheatmap.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="iheatmap",session=session)
            filename=session["filename"]
            flash(tb_str,'traceback')
            if not plot_arguments:
                plot_arguments=session["plot_arguments"]
            return render_template('/apps/iheatmap.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            #pio.orca.config.executable='/miniconda/bin/orca'
            #pio.orca.config.use_xvfb = True
            #pio.orca.config.save()
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            fig.write_image(figfile, format=plot_arguments["downloadf"], height=float(plot_arguments["fig_height"]) , width=float(plot_arguments["fig_width"]))
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure iheatmap")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        if download == "clusters":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            # CALL FIGURE FUNCTION

            fig, cols_cluster_numbers, index_cluster_numbers, df_=make_figure(df,plot_arguments)

            excelfile = io.BytesIO()
            EXC=pd.ExcelWriter(excelfile)
            df_.to_excel(EXC,sheet_name="heatmap",index=None)
            if type(cols_cluster_numbers) != type(None):
                cols_cluster_numbers.to_excel(EXC,sheet_name="rows",index=None)
            if type(index_cluster_numbers) != type(None):
                index_cluster_numbers.to_excel(EXC,sheet_name="cols",index=None)
            EXC.save()
            excelfile.seek(0)

            eventlog = UserLogging(email=current_user.email,action="download figure heatmap clusters")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")
        
        return render_template('apps/iheatmap.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])