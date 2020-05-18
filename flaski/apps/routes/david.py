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
from flaski.routes import FREEAPPS
from flaski.apps.main import icellplot
from flaski.email import send_exception_email


import os
import io
import sys
import random
import json

import pandas as pd

import base64

@app.route('/david/<download>', methods=['GET', 'POST'])
@app.route('/david', methods=['GET', 'POST'])
@login_required
def david(download=None):

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
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)

            session_=json.load(inputsessionfile)
            if session_["ftype"]!="session":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not a session file. Please make sure you upload a session file."
                flash(error_msg,'error')
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)

            if session_["app"]!="david":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not load as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)
    
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
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)

            session_=json.load(inputargumentsfile)
            if session_["ftype"]!="arguments":
                plot_arguments=session["plot_arguments"]
                error_msg="The file you have uploaded is not an arguments file. Please make sure you upload an arguments file."
                flash(error_msg,'error')
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)

            if session_["app"]!="heatmap":
                plot_arguments=session["plot_arguments"]
                error_msg="The file was not loaded as it is associated with the '%s' and not with this app." %session_["app"]
                flash(error_msg,'error')
                return render_template('/apps/david.html' , apps=apps, **plot_arguments)

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
            ### WORKING HERE
            values_list=[ s for s in list(plot_arguments.keys()) if "_value" in s ]
            values_list=[ s for s in values_list if type(plot_arguments[s]) == list ]
            for a in list(plot_arguments.keys()):
                if ( a in list(request.form.keys()) ) & ( a not in session["notUpdateList"] ):
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

        plot_arguments=session["plot_arguments"]

        if plot_arguments["user"] == "":
            flash('Please give in a register DAVID email in "Input" > "DAVID registered email". If you do not yet have a registered address you need to register with DAVID - https://david.ncifcrf.gov/webservice/register.htm. Please be aware that you will not receive any confirmation email. ','error')
            return render_template('/apps/david.html', apps=apps, **plot_arguments)
        
        # debug bad gateway
        # import time
        # time.sleep(30)

        # flash('30 seconds debug')
        # return render_template('/apps/david.html', apps=apps, **plot_arguments)

        # CALL FIGURE FUNCTION
        try:
            david_df, report_stats=run_david(plot_arguments)
        
            ## get this into json like in former apps
            david_df=david_df.astype(str)
            report_stats=report_stats.astype(str)
            session["david_df"]=david_df.to_json()
            session["report_stats"]=report_stats.to_json()
            #flash('Success!')

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
            session["david_in_store"]=True
            return render_template('/apps/david.html', david_in_store=True, apps=apps, table_headers=table_headers, david_contents=david_contents, **plot_arguments)

        except Exception as e:
            send_exception_email(user=current_user, eapp="david", emsg=e, etime=str(datetime.now())  )
            flash(e,'error')
            session["david_in_store"]=False
            return render_template('/apps/david.html', david_in_store=True, apps=apps, **plot_arguments)

    else:

        if download == "download":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            david_df=pd.read_json(session["david_df"])
            report_stats=pd.read_json(session["report_stats"])


            eventlog = UserLogging(email=current_user.email,action="download david")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                david_df.to_excel(EXC,sheet_name="david",index=None)
                report_stats.to_excel(EXC,sheet_name="stats",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(david_df.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["download_name"]})
                #outfile.seek(0)


            #mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename=plot_arguments["downloadn"]+".xlsx" 
            #print(plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"])
            #sys.stdout.flush()

        if download == "cellplot":
            # READ INPUT DATA FROM SESSION JSON
            david_df=pd.read_json(session["david_df"])
            david_df=david_df.astype(str)

            # INITIATE SESSION
            session["filename"]="<from DAVID>"
            session["ge_filename"]="Select file.."

            plot_arguments, lists, notUpdateList, checkboxes=icellplot.figure_defaults()

            session["plot_arguments"]=plot_arguments
            session["lists"]=lists
            session["notUpdateList"]=notUpdateList
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="icellplot"
            session["checkboxes"]=checkboxes

            session["df"]=david_df.to_json()

            cols=david_df.columns.tolist()
            session["plot_arguments"]["david_cols"]=["select a column.."]+cols
            session["plot_arguments"]["annotation_column"]=["none"]+cols
            session["plot_arguments"]["categories_to_plot"]=list(set(david_df["Category"].tolist()))
            session["plot_arguments"]["categories_to_plot_value"]=list(set(david_df["Category"].tolist()))
            
            return render_template('/apps/icellplot.html', filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)


        if "app" not in list(session.keys()):
            return_to_plot=False
        elif session["app"] != "david" :
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
            session["app"]="david"
            session["checkboxes"]=checkboxes

        eventlog = UserLogging(email=current_user.email, action="visit david")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/david.html',  apps=apps, **session["plot_arguments"])
