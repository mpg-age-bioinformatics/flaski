from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.david import run_david, figure_defaults
from flaski.models import User, UserLogging
from flaski.apps.main import icellplot
from flaski.email import send_exception_email
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request, read_tables, allowed_file, read_argument_file, read_session_file


import os
import io
import sys
import random
import json

import pandas as pd
import numpy as np

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

@app.route('/david/<download>', methods=['GET', 'POST'])
@app.route('/david', methods=['GET', 'POST'])
@login_required
def david(download=None):

    apps=current_user.user_apps

    reset_info=check_session_app(session,"david",apps)
    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        session["filename"]="Select file.."

        plot_arguments=figure_defaults()

        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="david"

    if request.method == 'POST' :

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"david")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/david.html' , filename=session["filename"],apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"david")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/david.html' , filename=session["filename"], apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                plot_arguments=read_request(request)

            if plot_arguments["user"] == "":
                flash('Please give in a register DAVID email in "Input" > "DAVID registered email". If you do not yet have a registered address you need to register with DAVID - https://david.ncifcrf.gov/webservice/register.htm. Please be aware that you will not receive any confirmation email. ','error')
                return render_template('/apps/david.html', apps=apps, **plot_arguments)

            # CALL FIGURE FUNCTION
            david_df, report_stats, msg=run_david(plot_arguments)
            if msg:
                flash(msg,"error")
                return render_template('/apps/david.html', apps=apps, **plot_arguments)

            # if (not david_df) and (not report_stats):
            #     flash("DAVID doesn't seem to recognize your email account. Make sure you have registered your account on https://david.ncifcrf.gov/webservice/register.htm. If you have just registered please be aware that it might take some hours for you account to be in their systems. Please try again later.",'error')
            #     return render_template('/apps/david.html', apps=apps, **plot_arguments)
        
            ## get this into json like in former apps
            david_df=david_df.astype(str)
            report_stats=report_stats.astype(str)
            # mapped=mapped.astype(str)

            session["david_df"]=david_df.to_json()
            session["report_stats"]=report_stats.to_json()
            # session["mapped"]=mapped.to_json()

            table_headers=david_df.columns.tolist()
            tmp=david_df[:50]
            for col in ["%","Fold Enrichment"]:
                tmp[col]=tmp[col].apply(lambda x: "{0:.2f}".format(float(x)))
            for col in ["PValue","Bonferroni","Benjamini","FDR"]:
                tmp[col]=tmp[col].apply(lambda x: '{:.2e}'.format(float(x)))
            for col in ["Genes"]+table_headers[13:]:
                tmp[col]=tmp[col].apply(lambda x: str(x)[:40]+"..")
            david_contents=[]
            for i in tmp.index.tolist():
                david_contents.append(list(tmp.loc[i,]))

            # david_in_store
            if len(david_df)>0:
                session["david_in_store"]=True
                return render_template('/apps/david.html', david_in_store=True, apps=apps, table_headers=table_headers, david_contents=david_contents, **plot_arguments)

            elif "david_in_store" in list(session.keys()):
                del(session["david_in_store"])
                return render_template('/apps/david.html', apps=apps, table_headers=table_headers, david_contents=david_contents, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="david",session=session)
            flash(tb_str,'traceback')
            if "david_in_store" in list(session.keys()):
                del(session["david_in_store"])
            return render_template('/apps/david.html', apps=apps, **plot_arguments)

    else:

        if download == "download":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            try:
                david_df=pd.read_json(session["david_df"])
                report_stats=pd.read_json(session["report_stats"])
            except:
                flash("No DAVID table in memory.",'error')
                return render_template('/apps/david.html', apps=apps, **plot_arguments)
            # mapped=pd.read_json(session["mapped"])
            # mapped=mapped.replace("nan",np.nan)

            eventlog = UserLogging(email=current_user.email,action="download david")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                def getGOID(x):
                    if "GO:" in x :
                        r=x.split("~")[0]
                    else:
                        r=np.nan
                    return r
                
                revigo=david_df[["Term","PValue"]]
                revigo["Term"]=revigo["Term"].apply(lambda x: getGOID(x) )
                revigo=revigo.dropna()
                
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                david_df.to_excel(EXC,sheet_name="david",index=None)
                report_stats.to_excel(EXC,sheet_name="stats",index=None)
                revigo.to_excel(EXC,sheet_name="revigo",index=None)
                # mapped.to_excel(EXC,sheet_name="mapped",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(david_df.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["download_name"]})
                #outfile.seek(0)

        if download == "cellplot":
            # READ INPUT DATA FROM SESSION JSON
            david_df=pd.read_json(session["david_df"])
            david_df=david_df.astype(str)

            reset_info=check_session_app(session,"icellplot",apps)
            if reset_info:
                flash(reset_info,'error')

            # INITIATE SESSION
            session["filename"]="<from DAVID>"
            session["ge_filename"]="Select file.."

            plot_arguments=icellplot.figure_defaults()

            session["plot_arguments"]=plot_arguments
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="icellplot"

            david_df=david_df.astype(str)
            session["df"]=david_df.to_json()

            cols=david_df.columns.tolist()
            session["plot_arguments"]["david_cols"]=["select a column.."]+cols
            session["plot_arguments"]["annotation_column"]=["none"]+cols
            session["plot_arguments"]["categories_to_plot"]=list(set(david_df["Category"].tolist()))
            session["plot_arguments"]["categories_to_plot_value"]=list(set(david_df["Category"].tolist()))
            
            return render_template('/apps/icellplot.html', filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)
        
        return render_template('apps/david.html',  apps=apps, **session["plot_arguments"])
