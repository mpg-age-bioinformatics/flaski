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
from flaski.routes import FREEAPPS
from flaski.email import send_exception_email
from flaski.routines import check_session_app

import os
import io
import sys
import random
import json

import pandas as pd

import base64


def getcomma(x):
    x=list( set(x) )
    x.sort()
    x=', '.join( x )
    return x

@app.route('/aarnaseqlake/<download>', methods=['GET', 'POST'])
@app.route('/aarnaseqlake', methods=['GET', 'POST'])
@login_required
def aarnaseqlake(download=None):

    reset_info=check_session_app(session,"aarnaseqlake")
    if reset_info:
        flash(reset_info,'error')

    apps=FREEAPPS+session["PRIVATE_APPS"]

    if request.method == 'POST':

        # USER INPUT/PLOT_ARGUMENTS GETS UPDATED TO THE LATEST INPUT
        # WITH THE EXCEPTION OF SELECTION LISTS
        plot_arguments = session["plot_arguments"]
        values_list=[ s for s in list(plot_arguments.keys()) if type(plot_arguments[s]) == list ]
        for a in list(plot_arguments.keys()):
            if a in list(request.form.keys()):
                if a in values_list:
                    plot_arguments[a]=request.form.getlist(a)
                else:
                    plot_arguments[a]=request.form[a]

        # checkboxes
        # for checkbox in session["checkboxes"]:
        #     if checkbox in list(request.form.keys()) :
        #         plot_arguments[checkbox]="on"
        #     else:
        #         try:
        #             plot_arguments[checkbox]=request.form[checkbox]
        #         except:
        #             if (plot_arguments[checkbox][0]!="."):
        #                 plot_arguments[checkbox]="off"

        # UPDATE SESSION VALUES
        session["plot_arguments"]=plot_arguments

        plot_arguments=session["plot_arguments"]

        results_files=pd.read_json(plot_arguments["results_files"])

        pa={}
        for selection in ["data_sets","groups","reps","gene_names","gene_ids"]:
            if "all" in plot_arguments["selected_%" %(selection)]:
                pa[selection]=plot_arguments["available_%" %(selection)]
            else:
                pa[selection]=plot_arguments["selected_%" %(selection)]

        # ['File', 'Set', 'IDs', 'Reps', 'Group', 'Sample']
        selected_results_files=results_files[ ( results_files['Set'].isin( pa["data_sets"]) ) & \
                                            ( results_files['Reps'].isin( pa["reps"]) ) & \
                                            ( results_files['Group'].isin( pa["groups"]) ) ]

        if "all" not in plot_arguments["selected_data_sets"]:
            selected_data_sets=list(set(selected_results_files['Set'].tolist()))
            selected_data_sets.sort()
            plot_arguments["selected_data_sets"]=selected_data_sets
        else:
            plot_arguments["selected_data_sets"]=["all"]

        if "all" not in plot_arguments["selected_groups"]:
            selected_groups=list(set(selected_results_files['Group'].tolist()))
            selected_groups.sort()
            plot_arguments["selected_groups"]=selected_groups
        else:
            plot_arguments["selected_groups"]=["all"]

        if "all" not in plot_arguments["selected_reps"]:
            selected_reps=list(set(selected_results_files['Reps'].tolist()))
            selected_reps.sort()
            plot_arguments["selected_reps"]=selected_reps
        else:
            plot_arguments["selected_reps"]=["all"]


        results_files=pd.read_json(plot_arguments["genes"])

        selected_genes=genes[(genes["gene_name"].isin(pa["gene_names"])) ,\
                             (genes["gene_id"].isin(pa["gene_ids"])) ]

        
        if "all" not in plot_arguments["selected_gene_names"]:
            selected_gene_names=list(set(selected_genes['gene_name'].tolist()))
            selected_gene_names.sort()
            plot_arguments["selected_gene_names"]=selected_gene_names
        else:
            plot_arguments["selected_gene_names"]=["all"]

        if "all" not in plot_arguments["selected_gene_ids"]:
            selected_gene_ids=list(set(selected_genes['gene_id'].tolist()))
            selected_gene_ids.sort()
            plot_arguments["selected_gene_ids"]=selected_gene_id
        else:
            plot_arguments["selected_gene_ids"]=["all"]
    
        selected_results_files=selected_results_files.groupby(['Set'])['Reps'].apply(lambda x: getcomma(x) ).reset_index()
        #selected_results_files.columns=["Dataset","Samples"]
        selected_results_files=list(selected_results_files.values)
        selected_results_files=[ list(s) for s in selected_results_files ]
        plot_arguments["selected_results_files"]=selected_results_files

        # data_sets groups reps gene_names gene_ids | available_ selected_

        #return render_template('/apps/david.html', david_in_store=True, apps=apps, table_headers=table_headers, david_contents=david_contents, **plot_arguments)

        return render_template('/apps/aarnaseqlake.html', apps=apps, **plot_arguments)

        # except Exception as e:
        #     send_exception_email(user=current_user, eapp="david", emsg=e, etime=str(datetime.now())  )
        #     flash(e,'error')
        #     session["david_in_store"]=False
        #     return render_template('/apps/david.html', david_in_store=True, apps=apps, **plot_arguments)

    else:

        # if download == "download":

        #     plot_arguments=session["plot_arguments"]

        #     # READ INPUT DATA FROM SESSION JSON
        #     david_df=pd.read_json(session["david_df"])
        #     report_stats=pd.read_json(session["report_stats"])


        #     eventlog = UserLogging(email=current_user.email,action="download david")
        #     db.session.add(eventlog)
        #     db.session.commit()

        #     if plot_arguments["download_format_value"] == "xlsx":
        #         outfile = io.BytesIO()
        #         EXC=pd.ExcelWriter(outfile)
        #         david_df.to_excel(EXC,sheet_name="david",index=None)
        #         report_stats.to_excel(EXC,sheet_name="stats",index=None)
        #         EXC.save()
        #         outfile.seek(0)
        #         return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"],as_attachment=True )

        #     elif plot_arguments["download_format_value"] == "tsv":               
        #         return Response(david_df.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %plot_arguments["download_name"]})
        #         #outfile.seek(0)


        #     #mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, attachment_filename=plot_arguments["downloadn"]+".xlsx" 
        #     #print(plot_arguments["download_name"]+ "." + plot_arguments["download_format_value"])
        #     #sys.stdout.flush()

        # if download == "cellplot":
        #     # READ INPUT DATA FROM SESSION JSON
        #     david_df=pd.read_json(session["david_df"])
        #     david_df=david_df.astype(str)

        #     # INITIATE SESSION
        #     session["filename"]="<from DAVID>"
        #     session["ge_filename"]="Select file.."

        #     plot_arguments, lists, notUpdateList, checkboxes=icellplot.figure_defaults()

        #     session["plot_arguments"]=plot_arguments
        #     session["lists"]=lists
        #     session["notUpdateList"]=notUpdateList
        #     session["COMMIT"]=app.config['COMMIT']
        #     session["app"]="icellplot"
        #     session["checkboxes"]=checkboxes

        #     session["df"]=david_df.to_json()

        #     cols=david_df.columns.tolist()
        #     session["plot_arguments"]["david_cols"]=["select a column.."]+cols
        #     session["plot_arguments"]["annotation_column"]=["none"]+cols
        #     session["plot_arguments"]["categories_to_plot"]=list(set(david_df["Category"].tolist()))
        #     session["plot_arguments"]["categories_to_plot_value"]=list(set(david_df["Category"].tolist()))
            
        #     return render_template('/apps/icellplot.html', filename=session["filename"], ge_filename=session["ge_filename"], apps=apps, **plot_arguments)


        if "app" not in list(session.keys()):
            return_to_plot=False
        elif session["app"] != "aarnaseqlake" :
            return_to_plot=False
        else:
            return_to_plot=True

        if not return_to_plot:
            # INITIATE SESSION
            session["filename"]="Select file.."

            session["plot_arguments"]["path_to_files"]="/flaski_private/aarnaseqlake/"

            gedf.read_csv(session["plot_arguments"]["path_to_files"]+"gene_expression.tsv",sep="\t")
            gedf=gedf.astype(str)
            session["plot_arguments"]["gedf"]=gedf.to_json()

            GO.read_csv(session["plot_arguments"]["path_to_files"]+"GO.tsv",sep="\t")
            GO=GO.astype(str)
            session["plot_arguments"]["GO"]=GO.to_json()

            results_files.read_csv(session["plot_arguments"]["path_to_files"]+"files2ids.tsv",sep="\t")
            results_files=results_files.astype(str)
            session["plot_arguments"]["results_files"]=results_files.to_json()

            genes.read_csv(session["plot_arguments"]["path_to_files"]+"genes.tsv",sep="\t")
            genes=results_files.astype(str)
            session["plot_arguments"]["results_files"]=genes.to_json()

            # with open(session["plot_arguments"]["path_to_files"]+"id_name.json","r") as f:
            #     id_name=json.load(f)
            # with open(session["plot_arguments"]["path_to_files"]+"ids2reps.json","r") as f:
            #     ids2reps=json.load(f)
            # with open(session["plot_arguments"]["path_to_files"]+"reps2ids.json","r") as f:
            #     reps2ids=json.load(f)
            # with open(session["plot_arguments"]["path_to_files"]+"sets2groups.json","r") as f:
            #     sets2groups=json.load(f)
            # with open(session["plot_arguments"]["path_to_files"]+"groups.json","r") as f:
            #     groups=json.load(f)


            available_data_sets=list(set(results_files["Set"].tolist()))
            available_data_sets.sort()
            session["plot_arguments"]["available_data_sets"]=["all"]+available_data_sets
            session["plot_arguments"]["selected_data_sets"]=["all"]

            groups=list(set(results_files["Group"].tolist()))
            groups.sort()
            session["plot_arguments"]["available_groups"]=groups
            session["plot_arguments"]["selected_groups"]=["all"]

            available_reps=list(set(results_files["Reps"].tolist()))
            available_reps.sort()
            session["plot_arguments"]["available_reps"]=["all"]+available_reps
            session["plot_arguments"]["selected_reps"]=["all"]

            available_gene_names=list(set(genes["gene_name"].tolist()))
            available_gene_names.sort()
            session["plot_arguments"]["available_gene_names"]=["all"]+available_gene_names
            session["plot_arguments"]["selected_gene_names"]=["all"]

            available_gene_ids=list(set(genes["gene_id"].tolist()))
            available_gene_ids.sort()
            session["plot_arguments"]["available_gene_ids"]=["all"]+available_gene_ids
            session["plot_arguments"]["selected_gene_ids"]=["all"]

            selected_results_files=results_files.groupby(['Set'])['Reps'].apply(lambda x: getcomma(x) ).reset_index()
            #selected_results_files.columns=["Dataset","Samples"]
            selected_results_files=list(selected_results_files.values)
            selected_results_files=[ list(s) for s in selected_results_files ]
            plot_arguments["selected_results_files"]=selected_results_files

            # data_sets groups reps gene_names gene_ids | available_ selected_

            session["COMMIT"]=app.config['COMMIT']
            session["app"]="aarnaseqlake"

        eventlog = UserLogging(email=current_user.email, action="visit aarnaseqlake")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])
