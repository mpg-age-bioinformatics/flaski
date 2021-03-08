from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.icellplot import make_figure, figure_defaults
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

@app.route('/icellplot/<download>', methods=['GET', 'POST'])
@app.route('/icellplot', methods=['GET', 'POST'])
@login_required
def icellplot(download=None):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       
    apps=current_user.user_apps
    plot_arguments=None  

    reset_info=check_session_app(session,"icellplot",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."
        session["ge_filename"]="Select file.."

        plot_arguments=figure_defaults()

        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="icellplot"

    if request.method == 'POST' :

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"icellplot")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/icellplot.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"icellplot")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                plot_arguments=read_request(request)
            
            missing_args=False
            # IF THE UPLOADS A NEW FILE 
            # THAN UPDATE THE SESSION FILE
            # READ INPUT FILE
            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):
                    df=read_tables(inputfile)
                    cols=df.columns.tolist()
                    session["plot_arguments"]["david_cols"]=["select a column.."]+cols
                    session["plot_arguments"]["annotation_column"]=["none"]+cols


                    # IF THE USER HAS NOT YET CHOSEN X AND Y VALUES THAN PLEASE SELECT
                    if (session["plot_arguments"]["terms_column"] not in cols) | (session["plot_arguments"]["terms_column"] == "select a column.."):
                        session["plot_arguments"]["terms_column"]="select a column.."
                        missing_args=True

                    if (session["plot_arguments"]["categories_column"] not in cols) | (session["plot_arguments"]["categories_column"] == "select a column.."):
                        session["plot_arguments"]["categories_column"]="select a column.."
                        missing_args=True
                    else:
                        session["plot_arguments"]["categories_to_plot"]=list(set( df[session["plot_arguments"]["categories_column"]].tolist() ))
                        session["plot_arguments"]["categories_to_plot_value"]=list(set( df[session["plot_arguments"]["categories_column"]].tolist() ))

                    if (session["plot_arguments"]["david_gene_ids"] not in cols)  | (session["plot_arguments"]["david_gene_ids"] == "select a column..") :
                        session["plot_arguments"]["david_gene_ids"]="select a column.."
                        missing_args=True

                    if (session["plot_arguments"]["plotvalue"] not in cols) | (session["plot_arguments"]["plotvalue"] == "select a column..") :
                        session["plot_arguments"]["plotvalue"]="select a column.."
                        missing_args=True
    
                    if missing_args:                
                        sometext="Please select matching columns from DAVID file."
                        flash(sometext,'info')
                    
                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling DAVID's output again." %filename
                    flash(error_msg,'error')
                    session["filename"]="Select file.."

            annotation_columns=( session["plot_arguments"]["annotation_column_value"]!="none") & (session["plot_arguments"]["annotation2_column_value"]!="none")

            if (not annotation_columns ):
                ge_inputfile = request.files["ge_inputfile"]
                if ge_inputfile:
                    filename = secure_filename(ge_inputfile.filename)
                    if allowed_file(ge_inputfile.filename):
                        df=read_tables(ge_inputfile,session_key="ge_df", file_field="ge_filename")
                    
                        cols=df.columns.tolist()
                        session["plot_arguments"]["ge_cols"]=["select a column.."]+cols

                        # IF THE USER HAS NOT YET CHOSEN X AND Y VALUES THAN PLEASE SELECT
                        if (session["plot_arguments"]["gene_identifier"] not in cols) | (session["plot_arguments"]["gene_identifier"] == "select a column..") :
                            session["plot_arguments"]["gene_identifier"]="select a column.."
                            missing_args=True
                        if (session["plot_arguments"]["expression_values"] not in cols) | (session["plot_arguments"]["expression_values"] == "select a column..") :
                            session["plot_arguments"]["expression_values"]="select a column.."
                            missing_args=True
                        if (session["plot_arguments"]["gene_name"] not in cols) | (session["plot_arguments"]["gene_name"] == "select a column..") :
                            session["plot_arguments"]["gene_name"]="select a column.."
                            missing_args=True
        
                        if missing_args:                
                            sometext="Please select matching columns in gene expression file for mapping."
                            flash(sometext,'info')
                                
                    else:
                        # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                        error_message="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                        has the correct format and respective extension and try uploadling the gene expression file again." %filename
                        flash(error_message,'error')
                        session["ge_filename"]="Select file.."

            if ( (session["ge_filename"]=="Select file..") & (not annotation_columns ) ) | (session["filename"]=="Select file..")  :
                plot_arguments=session["plot_arguments"]
                return render_template('/apps/icellplot.html' , filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments) 

            if missing_args:
                plot_arguments=session["plot_arguments"]
                return render_template('/apps/icellplot.html', filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)
            
            annotation_columns=( session["plot_arguments"]["annotation_column_value"]!="none") & (session["plot_arguments"]["annotation2_column_value"]!="none")

            if ( "df" not in list(session.keys()) ) | ( ( "ge_df" not in list(session.keys())) & (not annotation_columns)  ):
                    error_message="No data to plot, please upload a data or session  file."
                    flash(error_msg,'error')
                    return render_template('/apps/icellplot.html' , filename=session["filename"], ge_filename=session["ge_filename"], apps=apps,  **plot_arguments)
    
            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])  
            if (annotation_columns) & ( "ge_df" not in list(session.keys())):
                ge_df=pd.DataFrame()
                session["ge_df"]=ge_df.to_json()
            ge_df=pd.read_json(session["ge_df"])
        
            # CALL FIGURE FUNCTION
            # try:
            fig=make_figure(df,ge_df, plot_arguments)

            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            return render_template('/apps/icellplot.html', figure_url=figure_url, filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="icellplot",session=session)
            flash(tb_str,'traceback')
            if not plot_arguments:
                plot_arguments=session["plot_arguments"]
            return render_template('/apps/icellplot.html', filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)

    else:
        if download == "download":
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            ge_df=pd.read_json(session["ge_df"])

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig=make_figure( df, ge_df, plot_arguments )

            pio.orca.config.executable='/miniconda/bin/orca'
            pio.orca.config.use_xvfb = True
            #pio.orca.config.save()
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}

            pa_={}
            for v in ["height","width"]:
                if plot_arguments[v] != "":
                    pa_[v]=None
                elif plot_arguments[v]:
                    pa_[v]=float(plot_arguments[v])
                else:
                    pa_[v]=None

            if pa_["height"]:
                if pa_["width"]:
                    fig.write_image( figfile, format=plot_arguments["downloadf"], height=pa_["height"] , width=pa_["width"] )
                else:
                    fig.write_image( figfile, format=plot_arguments["downloadf"] )
            else:
                fig.write_image( figfile, format=plot_arguments["downloadf"] )

            figfile.seek(0)  # rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure icellplot")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )
        
        return render_template('apps/icellplot.html',  filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **session["plot_arguments"])