from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.models import User, UserLogging
from flaski.email import send_exception_email
from flaski.routines import check_session_app, handle_exception, read_request, fuzzy_search, separate_apps

from fuzzywuzzy import process

from flaski.apps.main.kegg import make_figure, figure_defaults

import os
import io
import sys
import random
import json

import numpy as np
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

@app.route('/kegg/<download>', methods=['GET', 'POST'])
@app.route('/kegg', methods=['GET', 'POST'])
@login_required
def kegg(download=None):

    apps=current_user.user_apps
    plot_arguments=None  

    # pa={}
    # pa["ids"]="HMDB00001\tred\nHMDB0004935\tred"
    # pa["species"]="mmu"

    # make_figure(pa)

    # return render_template('/index.html' ,apps=apps)

    reset_info=check_session_app(session,"kegg",apps)

    submissions, apps=separate_apps(current_user.user_apps)


    if reset_info:
        flash(reset_info,'error')
        # INITIATE SESSION
        plot_arguments=figure_defaults()

        print(plot_arguments)

        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="kegg"
  
    if request.method == 'POST' :

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"kegg")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/kegg.html' ,apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"kegg")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/kegg.html' , apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"] :
                plot_arguments=read_request(request)

            # CALL FIGURE FUNCTION
            df, msg=make_figure(plot_arguments)

            ## get this into json like in former apps
            df=df.astype(str)
            # mapped=mapped.astype(str)

            session["df"]=df.to_json()
            # session["mapped"]=mapped.to_json()

            # print(df.head())

            tmp=df[:50]
            table_headers=tmp.columns.tolist()

            def break_text(s,w=20):
               r=[s[i:i + w] for i in range(0, len(s), w)]
               r="".join(r)
               return r

            for c in ["ref_link","species_link"]:
               tmp[c]=tmp[c].apply(lambda x: break_text(x) )

            kegg_contents=[]
            for i in tmp.index.tolist():
                kegg_contents.append(list(tmp.loc[i,]))

            #print(kegg_contents[:2])
            # david_in_store
            if len(df)>0:
                session["kegg_in_store"]=True
                return render_template('/apps/kegg.html', kegg_in_store=True, apps=apps, table_headers=table_headers, kegg_contents=kegg_contents, **plot_arguments)

            elif "kegg_in_store" in list(session.keys()):
                del(session["kegg_in_store"])
                return render_template('/apps/kegg.html', apps=apps, table_headers=table_headers, kegg_contents=kegg_contents, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="kegg",session=session)
            flash(tb_str,'traceback')
            if "kegg_in_store" in list(session.keys()):
                del(session["kegg_in_store"])
            if not plot_arguments:
                plot_arguments=session["plot_arguments"]
            return render_template('/apps/kegg.html', apps=apps, **plot_arguments)

    else:

        if download == "download":

            plot_arguments=session["plot_arguments"]

            # READ INPUT DATA FROM SESSION JSON
            df=pd.read_json(session["df"])
            
            # mapped=pd.read_json(session["mapped"])
            # mapped=mapped.replace("nan",np.nan)

            eventlog = UserLogging(email=current_user.email,action="download kegg")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
               
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                df.to_excel(EXC,sheet_name="kegg",index=None)
                # mapped.to_excel(EXC,sheet_name="mapped",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":  
                return Response(df.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["download_name"]})
                #outfile.seek(0)
        
        return render_template('apps/kegg.html',  apps=apps, **session["plot_arguments"])
