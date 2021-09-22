from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.igseaplot import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file, separate_apps
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

@app.route('/igseaplot/<download>', methods=['GET', 'POST'])
@app.route('/igseaplot', methods=['GET', 'POST'])
@login_required
def igseaplot(download=None):
    """ 
    renders the plot on the fly.
    https://gist.github.com/illume/1f19a2cf9f26425b1761b63d9506331f
    """       
    apps=current_user.user_apps
    plot_arguments=None  

    reset_info=check_session_app(session,"igseaplot",apps)
    submissions, apps=separate_apps(current_user.user_apps)


    if reset_info:
        flash(reset_info,'error')

        # INITIATE SESSION
        session["filename"]="Select file.."
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="igseaplot"

    if request.method == 'POST' :

        try:
            # READ SESSION FILE IF AVAILABLE 
            # AND OVERWRITE VARIABLES
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"igseaplot")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/igseaplot.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"igseaplot")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/igseaplot.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")
            
            # IF THE UPLOADS A NEW FILE 
            # THAN UPDATE THE SESSION FILE
            # READ INPUT FILE
            inputfile = request.files["inputfile"]
            if inputfile:
                filename = secure_filename(inputfile.filename)
                if allowed_file(inputfile.filename):
                    df=read_tables(inputfile)
                    
                    cols=df.columns.tolist()

                    if len(cols) < 2 :
                        error_msg="Your table needs to have at least 2 columns. One for the x- and one for the y-value."
                        flash(error_msg,'error')
                        return render_template('/apps/igseaplot.html' , filename=session["filename"], apps=apps, **plot_arguments)

                    columns_select=["labels_col","gseacolor_cols","gsea_linewidth_cols",]
                    for parg in columns_select:
                        if session["plot_arguments"]["labels_col"] not in cols:
                            session["plot_arguments"][parg]=["select a column.."]+cols
                        
                    session["plot_arguments"]["xcols"]=cols
                    session["plot_arguments"]["ycols"]=cols

                    # IF THE USER HAS NOT YET CHOOSEN X AND Y VALUES THAN PLEASE SELECT
                    if (session["plot_arguments"]["xvals"] not in cols) | (session["plot_arguments"]["yvals"] not in cols):

                        session["plot_arguments"]["xvals"]=cols[0]
                        session["plot_arguments"]["yvals"]=cols[1]
                                    
                        sometext="Please select which values should map to the x and y axes."
                        plot_arguments=session["plot_arguments"]
                        flash(sometext,'info')
                        return render_template('/apps/igseaplot.html' , filename=filename, apps=apps,**plot_arguments)
                        
                    plot_arguments=session["plot_arguments"]
                    flash("New file uploaded.",'info')
                    return render_template('/apps/igseaplot.html' , filename=filename, apps=apps,**plot_arguments)

                else:
                    # IF UPLOADED FILE DOES NOT CONTAIN A VALID EXTENSION PLEASE UPDATE
                    error_msg="You can can only upload files with the following extensions: 'xlsx', 'tsv', 'csv'. Please make sure the file '%s' \
                    has the correct format and respective extension and try uploadling it again." %filename
                    flash(error_msg,'error')
                    return render_template('/apps/igseaplot.html' , filename="Select file..", apps=apps, **plot_arguments)
            
            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                # SELECTION LISTS DO NOT GET UPDATED 
                # lists=session["lists"]

                # USER INPUT/PLOT_ARGUMENTS GETS UPDATED TO THE LATEST INPUT
                # WITH THE EXCEPTION OF SELECTION LISTS
                plot_arguments = session["plot_arguments"]
                
                if request.form["labels_col_value"] != "select a column.." :
                    df=pd.read_json(session["df"])
                    plot_arguments["available_labels"] = list(set( df[ request.form["labels_col_value"] ].tolist() ))

                session["plot_arguments"]=plot_arguments
                plot_arguments=read_request(request)

            if "df" not in list(session.keys()):
                error_msg="No data to plot, please upload a data or session  file."
                flash(error_msg,'error')
                return render_template('/apps/igseaplot.html' , filename="Select file..", apps=apps,  **plot_arguments)

            # MAKE SURE WE HAVE THE LATEST ARGUMENTS FOR THIS SESSION
            filename=session["filename"]
            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])

            #CALL FIGURE FUNCTION
            fig=make_figure(df,plot_arguments)
            figure_url = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
            return render_template('/apps/igseaplot.html', figure_url=figure_url, filename=filename, apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="igseaplot",session=session)
            flash(tb_str,'traceback')
            if not plot_arguments:
                plot_arguments=session["plot_arguments"]
            filename=session["filename"]
            return render_template('/apps/igseaplot.html', filename=filename, apps=apps, **plot_arguments)

    else:
        if download == "download":
            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig=make_figure(df,plot_arguments)

            #pio.orca.config.executable='/miniconda/bin/orca'
            #pio.orca.config.use_xvfb = True
            #pio.orca.config.save()
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

            eventlog = UserLogging(email=current_user.email,action="download figure igseaplot")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )
        
        return render_template('apps/igseaplot.html',  filename=session["filename"], apps=apps, **session["plot_arguments"])