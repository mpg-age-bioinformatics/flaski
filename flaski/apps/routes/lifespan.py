from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.lifespan import make_figure, figure_defaults
from flaski.apps.main import iscatterplot
from flaski.models import User, UserLogging
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file
import plotly
import plotly.io as pio
import matplotlib.pyplot as plt
from flaski.email import send_exception_email

import os
import io
import sys
import random
import json

import pandas as pd

import base64

# def nFormat(x):
#     if str(x) == "nan":
#         return ""
#     elif float(x) == 0:
#         return str(x)
#     elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
#         return str('{:.3e}'.format(float(x)))
#     else:
#         return str('{:.3f}'.format(float(x)))

@app.route('/lifespan/<download>', methods=['GET', 'POST'])
@app.route('/lifespan', methods=['GET', 'POST'])
@login_required
def lifespan(download=None):

    apps=current_user.user_apps

    reset_info=check_session_app(session,"lifespan",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="lifespan"

    if request.method == 'POST':

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"lifespan")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/lifespan.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"lifespan")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/lifespan.html' , filename=session["filename"], apps=apps, **plot_arguments)
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
                        return render_template('/apps/lifespan.html' , filename=filename, apps=apps, **plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/lifespan.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if "df" not in list(session.keys()):
                    error_message="No data to plot, please upload a data or session  file."
                    flash(error_message,'error')
                    return render_template('/apps/lifespan.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            # CALL FIGURE FUNCTION
            # try:
            df_ls, fig=make_figure(df,plot_arguments)

            df_ls=df_ls.astype(str)
            session["df_ls"]=df_ls.to_json()

            # TRANSFORM FIGURE TO BYTES AND BASE64 STRING
            figfile = io.BytesIO()
            plt.savefig(figfile, format='png')
            plt.close()
            figfile.seek(0)  # rewind to beginning of file
            figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

            #return render_template('/apps/lifespan.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

            df_selected=df_ls[:50]
            cols_to_format=df_selected.columns.tolist()
            table_headers=cols_to_format
            df_selected=list(df_selected.values)
            df_selected=[ list(s) for s in df_selected ]

            return render_template('/apps/lifespan.html', figure_url=figure_url, table_headers=table_headers, table_contents=df_selected, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="lifespan",session=session)
            filename=session["filename"]
            flash(tb_str,'traceback')
            return render_template('/apps/lifespan.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            df_ls, fig=make_figure(df,plot_arguments)

            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            plt.savefig(figfile, format=plot_arguments["download_fig"])
            plt.close()
            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure lifespan curve")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["download_fig"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["download_fig"] )

        if download == "results":

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            df_ls, fig=make_figure(df,plot_arguments)

            eventlog = UserLogging(email=current_user.email,action="download table survival analysis")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["downloadf"] == "xlsx":
                excelfile = io.BytesIO()
                EXC=pd.ExcelWriter(excelfile)
                df_ls.to_excel(EXC,sheet_name="survival_analysis", index=None)
                EXC.save()
                excelfile.seek(0)
                return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx",as_attachment=True)

            elif plot_arguments["downloadf"] == "tsv":               
                return Response(df_ls.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["downloadn"]})
        
            
        return render_template('apps/lifespan.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])            