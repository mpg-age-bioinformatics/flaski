from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.apps.main.venndiagram import make_figure, figure_defaults
from flaski.models import User, UserLogging
from flaski.routines import session_to_file, check_session_app, handle_exception, read_request

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

@app.route('/venndiagram/<download>', methods=['GET', 'POST'])
@app.route('/venndiagram', methods=['GET', 'POST'])
@login_required
def venndiagram(download=None):

    apps=apps=current_user.user_apps

    reset_info=check_session_app(session,"venndiagram",apps)

    if reset_info:
        flash(reset_info,'error')
        plot_arguments=figure_defaults()
        session["plot_arguments"]=plot_arguments
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="venndiagram"

    if request.method == 'POST' :

        try:
            if request.files["inputsessionfile"] :
                msg, plot_arguments, error=read_session_file(request.files["inputsessionfile"],"venndiagram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/venndiagram.html' , apps=apps, **plot_arguments)
                flash(msg,"info")

            if request.files["inputargumentsfile"] :
                msg, plot_arguments, error=read_argument_file(request.files["inputargumentsfile"],"venndiagram")
                if error:
                    flash(msg,'error')
                    return render_template('/apps/venndiagram.html' , apps=apps, **plot_arguments)
                flash(msg,"info")

            if not request.files["inputsessionfile"] and not request.files["inputargumentsfile"]:
                plot_arguments=read_request(request)
            
                i=0
                for set_index in ["set1","set2","set3"]:
                    if plot_arguments["%s_values" %set_index] != "":
                        i=i+1
            
                if i < 2:
                        error_msg="No data to plot, please upload data."
                        flash(error_msg,'error')
                        return render_template('/apps/venndiagram.html', apps=apps,  **plot_arguments)
    
            # make sure we have the latest given arguments
            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, df, pvalues=make_figure(plot_arguments)

            # TRANSFORM FIGURE TO BYTES AND BASE64 STRING
            figfile = io.BytesIO()
            plt.savefig(figfile, format='png')
            plt.close()
            figfile.seek(0)  # rewind to beginning of file
            figure_url = base64.b64encode(figfile.getvalue()).decode('utf-8')

            if pvalues:
                message="Hypergeometric test:<br><br>"
                for pvalue in list(pvalues.keys()):
                    samples_keys=list(pvalues[pvalue].keys())
                    message=message+str(pvalue)+":<br>"+\
                        "- %s: "%samples_keys[0]  + str(pvalues[pvalue][samples_keys[0]])+"<br>"+\
                        "- %s: "%samples_keys[1] + str(pvalues[pvalue][samples_keys[1]])+"<br>"+\
                        "- n common: " + str(pvalues[pvalue]["common"])+"<br>"+\
                        "- n total: " + str(int(pvalues[pvalue]["total"]))+"<br>"+\
                        "- p value: " + str(pvalues[pvalue]["p value"])+"<br><br>"

                flash(message)

            return render_template('/apps/venndiagram.html', figure_url=figure_url,apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="venndiagram",session=session)
            flash(tb_str,'traceback')
            return render_template('/apps/venndiagram.html', apps=apps, **session["plot_arguments"])

    else:
        if download == "download":

            plot_arguments=session["plot_arguments"]

            # CALL FIGURE FUNCTION
            fig, df, pvalues=make_figure(plot_arguments)

            #flash('Figure is being sent to download but will not be updated on your screen.')
            figfile = io.BytesIO()
            mimetypes={"png":'image/png',"pdf":"application/pdf","svg":"image/svg+xml"}
            plt.savefig(figfile, format=plot_arguments["downloadf"])
            plt.close()
            figfile.seek(0)  #rewind to beginning of file

            eventlog = UserLogging(email=current_user.email,action="download figure venndiagram")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(figfile, mimetype=mimetypes[plot_arguments["downloadf"]], as_attachment=True, attachment_filename=plot_arguments["downloadn"]+"."+plot_arguments["downloadf"] )

        if download == "data":

            plot_arguments=session["plot_arguments"]
            fig, df, pvalues=make_figure(plot_arguments)

            if pvalues: 
                message=pd.DataFrame()
                for pvalue in pvalues:
                    tmp=pd.DataFrame(pvalues[pvalue],index=[pvalue])
                    tmp.columns=["n group 1","n group 2","n common","n total","p value"]
                    message=pd.concat([message,tmp])

            excelfile = io.BytesIO()
            EXC=pd.ExcelWriter(excelfile)
            df.to_excel(EXC,sheet_name="venndiagram",index=None)
            if pvalues:
                message.to_excel(EXC, sheet_name="hyperg.test",index=True)
            EXC.save()
            excelfile.seek(0)

            eventlog = UserLogging(email=current_user.email,action="download figure venndiagram data")
            db.session.add(eventlog)
            db.session.commit()

            return send_file(excelfile, attachment_filename=plot_arguments["downloadn"]+".xlsx")

        eventlog = UserLogging(email=current_user.email, action="visit venndiagram")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/venndiagram.html', apps=apps, **session["plot_arguments"])