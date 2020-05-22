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
from flaski.routes import FREEAPPS
from flaski.routines import check_session_app
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

ALLOWED_EXTENSIONS=["xlsx","tsv","csv"]
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/icellplot/<download>', methods=['GET', 'POST'])
@app.route('/icellplot', methods=['GET', 'POST'])
@login_required
def icellplot(download=None):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       

    reset_info=check_session_app(session,"icellplot")
    if reset_info:
        flash(reset_info,'error')

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
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

            session_=json.load(inputsessionfile)
            if session_["ftype"]!="session":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
                flash(error_msg,'error')
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

            if session_["app"]!="icellplot":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)
    
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
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

            session_=json.load(inputargumentsfile)
            if session_["ftype"]!="arguments":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
                flash(error_msg,'error')
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

            if session_["app"]!="icellplot":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/icellplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

            del(session_["ftype"])
            del(session_["COMMIT"])
            del(session_["PRIVATE_APPS"])
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
            values_list=[ s for s in list(plot_arguments.keys()) if "_value" in s ]
            values_list=[ s for s in values_list if type(plot_arguments[s]) == list ]
            for a in list(plot_arguments.keys()):
                if ( a in list(request.form.keys()) ) & ( a not in list(lists.keys())+session["notUpdateList"] ):
                    if a in values_list:
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

        
        missing_args=False
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
                    df=pd.read_excel(filestream, index_col=False, dtype=str)
                elif extension == "csv":
                    df=pd.read_csv(filestream, index_col=False, dtype=str)
                elif extension == "tsv":
                    df=pd.read_csv(filestream,sep="\t", index_col=False, dtype=str)
                
                session["df"]=df.to_json()
                                
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
                    session["ge_filename"]=filename
                    fileread = ge_inputfile.read()
                    filestream=io.BytesIO(fileread)
                    extension=filename.rsplit('.', 1)[1].lower()
                    if extension == "xlsx":
                        df=pd.read_excel(filestream, index_col=False)
                    elif extension == "csv":
                        df=pd.read_csv(filestream, index_col=False)
                    elif extension == "tsv":
                        df=pd.read_csv(filestream,sep="\t", index_col=False)
                    
                    df=df.astype(str)
                    session["ge_df"]=df.to_json()
                    
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
                    flash(error_msg,'error')
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
        try:
            fig=make_figure(df,ge_df, plot_arguments)

            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

            return render_template('/apps/icellplot.html', figure_url=figure_url, filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)

        except Exception as e:
            send_exception_email( user=current_user, eapp="icellplot", emsg=e, etime=str(datetime.now()) )
            flash(e,'error')
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
            #flash('Figure is being sent to download but will not be updated on your screen.')
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


        if "app" not in list(session.keys()):
            return_to_plot=False
        elif session["app"] != "icellplot" :
            return_to_plot=False
        else:
            return_to_plot=True

        if not return_to_plot:
            # INITIATE SESSION
            session["filename"]="Select file.."
            session["ge_filename"]="Select file.."

            plot_arguments, lists, notUpdateList, checkboxes=figure_defaults()

            session["plot_arguments"]=plot_arguments
            session["lists"]=lists
            session["notUpdateList"]=notUpdateList
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="icellplot"
            session["checkboxes"]=checkboxes

        eventlog = UserLogging(email=current_user.email, action="visit icellplot")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/icellplot.html',  filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **session["plot_arguments"])