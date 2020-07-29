from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.tsne import make_figure, figure_defaults
from flaski.apps.main import iscatterplot
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

def nFormat(x):
    if str(x) == "nan":
        return ""
    elif float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))

@app.route('/tsne/<download>', methods=['GET', 'POST'])
@app.route('/tsne', methods=['GET', 'POST'])
@login_required
def tsne(download=None):

    apps=current_user.user_apps

    reset_info=check_session_app(session,"tsne",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="tsne"

    if request.method == 'POST':

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"tsne")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/tsne.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"tsne")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/tsne.html' , filename=session["filename"], apps=apps, **plot_arguments)
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
                        return render_template('/apps/tsne.html' , filename=filename, apps=apps, **plot_arguments)
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/tsne.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if "df" not in list(session.keys()):
                    error_message="No data to plot, please upload a data or session  file."
                    flash(error_message,'error')
                    return render_template('/apps/tsne.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            # CALL FIGURE FUNCTION
            # try:
            df_tsne=make_figure(df,plot_arguments)

            df_tsne=df_tsne.astype(str)
            session["df_tsne"]=df_tsne.to_json()

            #features=features.astype(str)
            #session["features"]=features.to_json()

            df_selected=df_tsne[:50]
            cols_to_format=df_selected.columns.tolist()
            #cols_to_format=[ s for s in cols_to_format if s not in ["gene_id","gene_name"] ]
            table_headers=[cols_to_format[0]]
            for c in cols_to_format[1:]:
                df_selected[c]=df_selected[c].apply(lambda x: nFormat(x) )
                #new_name=c.split(" - ")[0]+" - "+nFormat(float(c.split(" - ")[-1].split("%")[0]))+"%"
                new_name=c
                table_headers.append(new_name)
            df_selected=list(df_selected.values)
            df_selected=[ list(s) for s in df_selected ]

            #features_selected=features[:50]
            #cols_to_format=features_selected.columns.tolist()
            #cols_to_format=[ s for s in cols_to_format if "key" not in s ]
            #features_headers=features_selected.columns.tolist()
            #for c in cols_to_format[1:]:
            #    features_selected[c]=features_selected[c].apply(lambda x: nFormat(x) )
            #features_selected=features_selected.astype(str)
            #features_selected=features_selected.replace("nan","")
            #features_selected=list(features_selected.values)
            #features_selected=[ list(s) for s in features_selected ]
            
            return render_template('/apps/tsne.html', table_headers=table_headers, table_contents=df_selected, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="tsne",session=session)
            filename=session["filename"]
            flash(tb_str,'traceback')
            return render_template('/apps/tsne.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df_tsne=pd.read_json(session["df_tsne"])
            #features=pd.read_json(session["features"])

            # CALL FIGURE FUNCTION

            eventlog = UserLogging(email=current_user.email,action="download table tsne values")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["downloadf"] == "xlsx":
                excelfile = io.BytesIO()
                EXC=pd.ExcelWriter(excelfile)
                df_tsne.to_excel(EXC,sheet_name="tsne", index=None)
                #features.to_excel(EXC,sheet_name="features", index=None)
                EXC.save()
                excelfile.seek(0)
                return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx",as_attachment=True)

            elif plot_arguments["downloadf"] == "tsv":               
                return Response(df_tsne.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["downloadn"]})
        
        if download == "scatter":

            # READ INPUT DATA FROM SESSION JSON
            df_tsne=pd.read_json(session["df_tsne"])

            reset_info=check_session_app(session,"iscatterplot",apps)
            if reset_info:
                flash(reset_info,'error')

            # INITIATE SESSION
            session["filename"]="<from tSNE>"
            plot_arguments=iscatterplot.figure_defaults()
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="iscatterplot"

            df_tsne=df_tsne.astype(str)
            session["df"]=df_tsne.to_json()

            plot_arguments["xcols"]=df_tsne.columns.tolist()
            plot_arguments["ycols"]=df_tsne.columns.tolist()
            plot_arguments["groups"]=plot_arguments["groups"]+df_tsne.columns.tolist()
            plot_arguments["labels_col"]=df_tsne.columns.tolist()

            plot_arguments["xvals"]=df_tsne.columns.tolist()[1]
            plot_arguments["yvals"]=df_tsne.columns.tolist()[2]
            plot_arguments["labels_col_value"]=df_tsne.columns.tolist()[0]
            plot_arguments["title"]="tSNE"
            plot_arguments["xlabel"]=df_tsne.columns.tolist()[1]
            plot_arguments["ylabel"]=df_tsne.columns.tolist()[2]

            session["plot_arguments"]=plot_arguments

            return render_template('/apps/iscatterplot.html', filename=session["filename"], apps=apps, **plot_arguments)

        return render_template('apps/tsne.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])            