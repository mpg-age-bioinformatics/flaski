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

from fuzzywuzzy import process

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

        results_files=pd.read_csv(session["plot_arguments"]["path_to_files"]+"files2ids.tsv",sep="\t")

        pa={}
        for selection in ["data_sets","groups","reps","gene_names","gene_ids"]:
            if "all" in plot_arguments["selected_%s" %(selection)]:
                pa[selection]=plot_arguments["available_%s" %(selection)]
            else:
                pa[selection]=plot_arguments["selected_%s" %(selection)]

        # ['File', 'Set', 'IDs', 'Reps', 'Group', 'Sample']
        selected_results_files=results_files[ ( results_files['Set'].isin( pa["data_sets"] ) ) & \
                                            ( results_files['Reps'].isin( pa["reps"] ) ) & \
                                            ( results_files['Group'].isin( pa["groups"] ) ) ]

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


        genes=pd.read_csv(session["plot_arguments"]["path_to_files"]+"genes.tsv",sep="\t")

        if plot_arguments["selected_gene_names"] != "":
            available_gene_names=plot_arguments["available_gene_names"]
            selected_gene_names=plot_arguments["selected_gene_names"].split(",")
            selected_gene_names=[ s.strip(" ") for s in selected_gene_names ]
            selected_gene_names.sort()
            found_gene_names=[ s  for s in selected_gene_names if s in available_gene_names ]
            not_found_gene_names=[ s for s in selected_gene_names if s not in found_gene_names ]
            best_matches={}
            for gene_name in not_found_gene_names:
                #best_match=process.extractOne(gene_name,available_gene_names)[0]
                best_match=process.extract(gene_name,available_gene_names)
                if gene_name.lower() == best_match[0][0].lower():
                    found_gene_names.append(best_match[0][0])
                else:
                    best_match=best_match[:3]
                    best_match=[ s[0] for s in best_match ]
                    best_matches[gene_name]=", ".join(best_match)
            if len(list(best_matches.keys())) > 0:
                emsg="The folowing gene names could not be found. Please consider the respective options: "
                for gene in list(best_matches.keys()):
                    emsg=emsg+gene+": "+best_matches[gene]+"; "
                emsg=emsg[:-2]+"."
                flash(emsg,'error')
            selected_gene_names=found_gene_names
        else:
            selected_gene_names=genes["gene_name"].tolist()

        if plot_arguments["selected_gene_ids"] != "":
            available_gene_ids=plot_arguments["available_gene_ids"]
            selected_gene_ids=plot_arguments["selected_gene_ids"].split(",")
            selected_gene_ids=[ s.strip(" ") for s in selected_gene_ids ]
            selected_gene_ids.sort()
            found_gene_ids=[ s  for s in selected_gene_ids if s in available_gene_ids ]
            not_found_gene_ids=[ s for s in selected_gene_ids if s not in fount_gene_ids ]
            best_matches={}
            for gene_id in not_found_gene_ids:
                #best_match=process.extractOne(gene_name,available_gene_names)[0]
                best_match=process.extract(gene_id,available_gene_ids)
                if gene_id.lower() == best_match[0][0].lower():
                    found_gene_ids.append(best_match[0][0])
                else:
                    best_match=best_match[:3]
                    best_match=[ s[0] for s in best_match ]
                    best_matches[gene_name]=", ".join(best_match)
            if len(list(best_matches.keys())) > 0:
                emsg="The folowing gene ids could not be found. Please consider the respective options: "
                for gene in list(best_matches.keys()):
                    emsg=emsg+gene+": "+best_matches[gene]+"; "
                emsg=emsg[:-2]+"."
                flash(emsg,'error')
            selected_gene_ids=found_gene_ids
        else:
            selected_gene_ids=genes["gene_id"].tolist()

        selected_genes=genes[(genes["gene_name"].isin(selected_gene_names)) & \
                             (genes["gene_id"].isin(selected_gene_ids)) ]
        print(selected_genes.head())

        if plot_arguments["selected_gene_ids"] != "":
            selected_gene_ids=list(set(selected_genes['gene_id'].tolist()))
            selected_gene_ids.sort()
            selected_gene_ids=", ".join(selected_gene_ids)
            plot_arguments["selected_gene_ids"]=selected_gene_ids

        if plot_arguments["selected_gene_names"] != "":
            selected_gene_names=list(set(selected_genes['gene_name'].tolist()))
            selected_gene_names.sort()
            selected_gene_names=", ".join(selected_gene_names)
            plot_arguments["selected_gene_names"]=selected_gene_names

        nsets=len(plot_arguments["selected_data_sets"])
        if nsets > 1:
            selected_results_files["Labels"]=selected_results_files["Set"]+"_"+selected_results_files["Reps"]
        else:
            selected_results_files["Labels"]=selected_results_files["Set"]
        ids2labels=selected_results_files[["IDs","Labels"]].drop_duplicates()
        ids2labels.index=ids2labels["IDs"].tolist()
        ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

        gedf=pd.read_csv(session["plot_arguments"]["path_to_files"]+"gene_expression.tsv",sep="\t",index_col=[0])
        selected_ge=gedf[list(ids2labels.keys())]
        
        selected_ge=pd.merge(selected_genes, selected_ge, left_on=["name_id"], right_index=True,how="left")
        selected_ge=selected_ge.drop(["name_id"],axis=1)
        selected_ge.reset_index(inplace=True,drop=True)
        selected_ge.rename(columns=ids2labels,inplace=True)
        plot_arguments["selected_ge_50"]=selected_ge[:50]


        selected_results_files=selected_results_files.groupby(['Set'])['Reps'].apply(lambda x: getcomma(x) ).reset_index()
        #selected_results_files.columns=["Dataset","Samples"]
        selected_results_files=list(selected_results_files.values)
        selected_results_files=[ list(s) for s in selected_results_files ]
        plot_arguments["selected_results_files"]=selected_results_files

        # data_sets groups reps gene_names gene_ids | available_ selected_

        #return render_template('/apps/david.html', david_in_store=True, apps=apps, table_headers=table_headers, david_contents=david_contents, **plot_arguments)

        session["plot_arguments"]=plot_arguments

        return render_template('/apps/aarnaseqlake.html', apps=apps, **plot_arguments)

        # except Exception as e:
        #     send_exception_email(user=current_user, eapp="david", emsg=e, etime=str(datetime.now())  )
        #     flash(e,'error')
        #     session["david_in_store"]=False
        #     return render_template('/apps/david.html', david_in_store=True, apps=apps, **plot_arguments)

    else:

        if download == "download":

            plot_arguments=session["plot_arguments"]

            selected_results_files=pd.read_json(plot_arguments["selected_results_files_"])





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

            session["plot_arguments"]={}

            session["plot_arguments"]["path_to_files"]="/flaski_private/aarnaseqlake/"

            gedf=pd.read_csv(session["plot_arguments"]["path_to_files"]+"gene_expression.tsv",sep="\t",index_col=[0])
            #session["plot_arguments"]["gedf"]=gedf.to_json()

            #GO=pd.read_csv(session["plot_arguments"]["path_to_files"]+"GO.tsv",sep="\t")
            #GO=GO.astype(str)
            #session["plot_arguments"]["GO"]=GO.to_json()

            results_files=pd.read_csv(session["plot_arguments"]["path_to_files"]+"files2ids.tsv",sep="\t")
            #results_files=results_files.astype(str)
            #session["plot_arguments"]["results_files"]=results_files.to_json()

            genes=pd.read_csv(session["plot_arguments"]["path_to_files"]+"genes.tsv",sep="\t")
            #genes=genes.astype(str)
            #session["plot_arguments"]["results_files"]=genes.to_json()

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
            session["plot_arguments"]["available_groups"]=["all"]+groups
            session["plot_arguments"]["selected_groups"]=["all"]

            available_reps=list(set(results_files["Reps"].tolist()))
            available_reps.sort()
            session["plot_arguments"]["available_reps"]=["all"]+available_reps
            session["plot_arguments"]["selected_reps"]=["all"]

            available_gene_names=list(set(genes["gene_name"].tolist()))
            available_gene_names.sort()
            session["plot_arguments"]["available_gene_names"]=available_gene_names
            session["plot_arguments"]["selected_gene_names"]=""

            available_gene_ids=list(set(genes["gene_id"].tolist()))
            available_gene_ids.sort()
            session["plot_arguments"]["available_gene_ids"]=available_gene_ids
            session["plot_arguments"]["selected_gene_ids"]=""

            selected_results_files=results_files.copy()
            selected_results_files["Labels"]=selected_results_files["Set"]+"_"+selected_results_files["Reps"]
            ids2labels=selected_results_files[["IDs","Labels"]].drop_duplicates()
            ids2labels.index=ids2labels["IDs"].tolist()
            ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

            selected_ge=gedf[ list(ids2labels.keys()) ]
            selected_genes=genes.copy()
            #print(selected_genes.head(), selected_ge.head() )
            selected_ge=pd.merge(selected_genes, selected_ge, left_on=["name_id"], right_index=True,how="left")
            selected_ge=selected_ge.drop(["name_id"],axis=1)
            selected_ge.reset_index(inplace=True,drop=True)
            selected_ge.rename(columns=ids2labels,inplace=True)
            #session["plot_arguments"]["selected_ge"]=selected_ge
            session["plot_arguments"]["selected_ge_50"]=selected_ge[:50]

            selected_results_files=results_files.groupby(['Set'])['Reps'].apply(lambda x: getcomma(x) ).reset_index()
            #selected_results_files.columns=["Dataset","Samples"]
            selected_results_files=list(selected_results_files.values)
            selected_results_files=[ list(s) for s in selected_results_files ]
            session["plot_arguments"]["selected_results_files"]=selected_results_files

            # data_sets groups reps gene_names gene_ids | available_ selected_

            session["plot_arguments"]["download_format"]=["tsv","xlsx"]
            session["plot_arguments"]["download_format_value"]="xlsx"
            session["plot_arguments"]["download_name"]="DAVID"
            session["plot_arguments"]["session_download_name"]="MySession.DAVID"
            session["plot_arguments"]["inputsessionfile"]="Select file.."
            session["plot_arguments"]["session_argumentsn"]="MyArguments.DAVID"
            session["plot_arguments"]["inputargumentsfile"]="Select file.."

            session["COMMIT"]=app.config['COMMIT']
            session["app"]="aarnaseqlake"

        eventlog = UserLogging(email=current_user.email, action="visit aarnaseqlake")
        db.session.add(eventlog)
        db.session.commit()
        
        return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])
