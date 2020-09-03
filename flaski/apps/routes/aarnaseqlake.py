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
from flaski.routines import check_session_app, handle_exception, read_request, fuzzy_search

from flaski.apps.main import iscatterplot, iheatmap

from fuzzywuzzy import process

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


def getcomma(x):
    x=list( set(x) )
    x.sort()
    x=', '.join( x )
    return x

def fix_go(x):
    if str(x)[0] == ",":
        return x[2:]
    else:
        return x

def nFormat(x):
    if float(x) == 0:
        return str(x)
    elif ( float(x) < 0.01 ) & ( float(x) > -0.01 ) :
        return str('{:.3e}'.format(float(x)))
    else:
        return str('{:.3f}'.format(float(x)))

def get_tables(plot_arguments):

    results_files=pd.read_csv(plot_arguments["path_to_files"]+"files2ids.tsv",sep="\t")

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

    if len(plot_arguments["selected_data_sets"]) == 0:
        plot_arguments["selected_data_sets"]=["all"]
    elif "all" not in plot_arguments["selected_data_sets"]:
        selected_data_sets=list(set(selected_results_files['Set'].tolist()))
        selected_data_sets.sort()
        plot_arguments["selected_data_sets"]=selected_data_sets
    else:
        plot_arguments["selected_data_sets"]=["all"]

    if len(plot_arguments["selected_groups"]) == 0:
        plot_arguments["selected_groups"]=["all"]
    elif "all" not in plot_arguments["selected_groups"]:
        selected_groups=list(set(selected_results_files['Group'].tolist()))
        selected_groups.sort()
        plot_arguments["selected_groups"]=selected_groups
    else:
        plot_arguments["selected_groups"]=["all"]

    if len(plot_arguments["selected_reps"]) == 0:
        plot_arguments["selected_reps"]=["all"]
    elif "all" not in plot_arguments["selected_reps"]:
        selected_reps=list(set(selected_results_files['Reps'].tolist()))
        selected_reps.sort()
        plot_arguments["selected_reps"]=selected_reps
    else:
        plot_arguments["selected_reps"]=["all"]


    genes=pd.read_csv(plot_arguments["path_to_files"]+"genes.tsv",sep="\t")

    if plot_arguments["selected_gene_names"] != "":
        selected_gene_names, emsg=fuzzy_search(plot_arguments["selected_gene_names"],plot_arguments["available_gene_names"])
        if emsg:
            flash(emsg,'error')
    else:
        selected_gene_names=genes["gene_name"].tolist()

    if plot_arguments["selected_gene_ids"] != "":
        selected_gene_ids, emsg=fuzzy_search(plot_arguments["selected_gene_ids"],plot_arguments["available_gene_ids"])
        if emsg:
            flash(emsg,'error')
    else:
        selected_gene_ids=genes["gene_id"].tolist()

    selected_genes=genes[(genes["gene_name"].isin(selected_gene_names)) & \
                        (genes["gene_id"].isin(selected_gene_ids)) ]

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

    if ( plot_arguments["selected_gene_ids"] != "" ) | (plot_arguments["selected_gene_names"] != ""):
        siggenesdf=pd.read_csv(session["plot_arguments"]["path_to_files"]+"significant.genes.tsv",sep="\t")
        siggenesdf=siggenesdf[ siggenesdf["gene_id"].isin( selected_genes["gene_id"].tolist() ) ]
        plot_arguments["siggenesdf_columns"]=siggenesdf.columns.tolist()
        siggenesdf_values=list(siggenesdf[:50].values)
        siggenesdf_values=[ list(s) for s in siggenesdf_values ]
        plot_arguments["siggenesdf_values"]=siggenesdf_values
    else:
        siggenesdf=None
        if "siggenesdf_values" in list(plot_arguments.keys()):
            del(plot_arguments["siggenesdf_columns"])
            del(plot_arguments["siggenesdf_values"])
    
    nsets=len(plot_arguments["selected_data_sets"])
    if (nsets > 1) | ("all" in plot_arguments["selected_data_sets"] ):
        selected_results_files["Labels"]=selected_results_files["Set"]+"_"+selected_results_files["Reps"]
    else:
        selected_results_files["Labels"]=selected_results_files["Reps"]
    ids2labels=selected_results_files[["IDs","Labels"]].drop_duplicates()
    ids2labels.index=ids2labels["IDs"].tolist()
    ids2labels=ids2labels[["Labels"]].to_dict()["Labels"]

    gedf=pd.read_csv(session["plot_arguments"]["path_to_files"]+"gene_expression.tsv",sep="\t",index_col=[0])
    selected_ge=gedf[list(ids2labels.keys())]
    
    selected_ge=selected_ge.astype(float)
    cols=selected_ge.columns.tolist()
    selected_ge["sum"]=selected_ge.sum(axis=1)
    selected_ge=selected_ge[selected_ge["sum"]>0]
    selected_ge=selected_ge.drop(["sum"],axis=1)
    selected_ge=pd.merge(selected_genes, selected_ge, left_on=["name_id"], right_index=True,how="left")
    selected_ge=selected_ge.dropna(subset=cols,how="all")
    selected_ge=selected_ge.drop(["name_id"],axis=1)
    # for c in cols:
    #     selected_ge[c]=selected_ge[c].apply(lambda x: nFormat(x) )
    selected_ge.reset_index(inplace=True,drop=True)
    selected_ge.rename(columns=ids2labels,inplace=True)
    df_ge=selected_ge.copy()
    selected_ge=selected_ge[:50]
    cols_to_format=selected_ge.columns.tolist()
    cols_to_format=[ s for s in cols_to_format if s not in ["gene_id","gene_name"] ]
    # print(type(selected_ge),selected_ge.head())
    for c in cols_to_format:
        selected_ge[c]=selected_ge[c].apply(lambda x: nFormat(x) )

    plot_arguments["selected_ge_50_cols"]=selected_ge.columns.tolist()

    selected_ge=list(selected_ge.values)
    selected_ge=[ list(s) for s in selected_ge ]
    session["plot_arguments"]["selected_ge_50"]=selected_ge

    ngroups=len(plot_arguments["selected_groups"])

    if len(plot_arguments["selected_data_sets"]) == 0 :
        emsg="You need to select at least one data set. Alternatively, you can select 'all'"
        flash(emsg,'error')

    if len(plot_arguments["selected_data_sets"]) == 0 :
        plot_arguments["selected_data_sets"]=["all"]

    if (ngroups == 2) & ( nsets == 1 ) & ( plot_arguments["selected_data_sets"][0] != "all" ):
        groups_to_files=pd.read_csv(plot_arguments["path_to_files"]+"metadata.tsv",sep="\t")

        selected_dge=groups_to_files[ (groups_to_files["Group_1"].isin(plot_arguments["selected_groups"]) ) & \
                                    (groups_to_files["Group_2"].isin(plot_arguments["selected_groups"]) ) & \
                                    (groups_to_files["Set"].isin(plot_arguments["selected_data_sets"])  )]["File"].tolist()[0]
        
        selected_dge=pd.read_csv(session["plot_arguments"]["path_to_files"]+"pairwise/"+selected_dge,sep="\t")#, index_col=[0])
        selected_dge=pd.merge(selected_genes[["gene_id"]], selected_dge, on=["gene_id"],how="inner")
        selected_dge=selected_dge.sort_values(by=["padj"],ascending=True)
        cols_to_format=selected_dge.columns.tolist()
        cols_to_format=[ s for s in cols_to_format if s not in ["gene_id","gene_name"] ]
        #cols=["baseMean","log2FoldChange","lfcSE","pvalue","padj"]
        #selected_dge=selected_dge[cols]
        #selected_dge=pd.merge(df_ge,selected_dge,left_on=["gene_id"],right_index=True, how="left")
        #selected_dge=selected_dge.dropna(subset=cols,how="all")

        plot_arguments["selected_dge_50_cols"]=selected_dge.columns.tolist()
        
        df_dge=selected_dge.copy()
        selected_dge=selected_dge[:50]
        for c in cols_to_format:
            selected_dge[c]=selected_dge[c].apply(lambda x: nFormat(x) )
        selected_dge=list(selected_dge.values)
        selected_dge=[ list(s) for s in selected_dge ]
        plot_arguments["selected_dge_50"]=selected_dge
                
    else:
        df_dge=None
        if "selected_dge" in list(plot_arguments.keys()):
            del(plot_arguments["selected_dge_50"])
            del(plot_arguments["selected_dge_50_cols"])
    


    selected_results_files=selected_results_files.groupby(['Set'])['Reps'].apply(lambda x: getcomma(x) ).reset_index()
    selected_results_files.columns=["Dataset","Samples"]
    df_metadata=selected_results_files.copy()
    selected_results_files=list(selected_results_files.values)
    selected_results_files=[ list(s) for s in selected_results_files ]
    plot_arguments["selected_results_files"]=selected_results_files

    return plot_arguments, df_metadata, df_dge, df_ge, siggenesdf


@app.route('/aarnaseqlake/<download>', methods=['GET', 'POST'])
@app.route('/aarnaseqlake', methods=['GET', 'POST'])
@login_required
def aarnaseqlake(download=None):

    apps=current_user.user_apps

    if "aarnaseqlake" not in [ s["link"] for s in apps ] :
        return redirect(url_for('index'))

    reset_info=check_session_app(session,"aarnaseqlake",apps)
    if reset_info:
        flash(reset_info,'error')

        # INITIATE SESSION
        session["filename"]="Select file.."
        session["plot_arguments"]={}
        session["plot_arguments"]["path_to_files"]="/flaski_private/aarnaseqlake/"
        gedf=pd.read_csv(session["plot_arguments"]["path_to_files"]+"gene_expression.tsv",sep="\t",index_col=[0])
        results_files=pd.read_csv(session["plot_arguments"]["path_to_files"]+"files2ids.tsv",sep="\t")
        genes=pd.read_csv(session["plot_arguments"]["path_to_files"]+"genes.tsv",sep="\t")

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

        session["plot_arguments"]["download_format"]=["tsv","xlsx"]
        session["plot_arguments"]["download_format_value"]="xlsx"
        session["plot_arguments"]["download_name"]="RNAseqLake"
        session["plot_arguments"]["session_download_name"]="MySession.RNAseqLake"
        session["plot_arguments"]["inputsessionfile"]="Select file.."
        session["plot_arguments"]["session_argumentsn"]="MyArguments.RNAseqLake"
        session["plot_arguments"]["inputargumentsfile"]="Select file.."

        plot_arguments=session["plot_arguments"]
        plot_arguments, df_metadata, df_dge, df_ge, siggenesdf=get_tables(plot_arguments)
        session["plot_arguments"]=plot_arguments

        session["COMMIT"]=app.config['COMMIT']
        session["app"]="aarnaseqlake"

    if request.method == 'POST':

        try:
            plot_arguments=read_request(request)
            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf=get_tables(plot_arguments)
            session["plot_arguments"]=plot_arguments

            return render_template('/apps/aarnaseqlake.html', apps=apps, **plot_arguments)

        except Exception as e:
            tb_str=handle_exception(e,user=current_user,eapp="aarnaseqlake",session=session)
            flash(tb_str,'traceback')
            return render_template('/apps/aarnaseqlake.html', apps=apps, **plot_arguments)

    else:

        if download == "metadata":

            plot_arguments=session["plot_arguments"]

            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf=get_tables(plot_arguments)

            eventlog = UserLogging(email=current_user.email,action="download aarnaseqlake")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                df_metadata.to_excel(EXC,sheet_name="metadata",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ ".metadata." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(df_metadata.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %(plot_arguments["download_name"]+".metadata")})


        if download == "siggenes":

            plot_arguments=session["plot_arguments"]

            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf=get_tables(plot_arguments)

            eventlog = UserLogging(email=current_user.email,action="download aarnaseqlake")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                siggenesdf.to_excel(EXC,sheet_name="sig.genes",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ ".siggenesdf." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(df_metadata.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %(plot_arguments["download_name"]+".siggenesdf")})


        if download == "geneexpression":

            plot_arguments=session["plot_arguments"]

            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf=get_tables(plot_arguments)

            GO=pd.read_csv(plot_arguments["path_to_files"]+"GO.tsv",sep="\t")
            GO.columns=["gene_id","go_id","go_name","go_definition"]
            # for c in GO.columns.tolist():
            #     GO[c]=GO[c].apply(lambda x: fix_go(x) )

            df_ge=pd.merge(df_ge, GO, on=["gene_id"], how="left")

            eventlog = UserLogging(email=current_user.email,action="download aarnaseqlake")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                df_ge.to_excel(EXC,sheet_name="geneexp.",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ ".gene_expression." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(df_ge.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %(plot_arguments["download_name"]+".gene_expression")})

        if download == "dge":

            plot_arguments=session["plot_arguments"]

            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf = get_tables(plot_arguments)

            GO=pd.read_csv(plot_arguments["path_to_files"]+"GO.tsv",sep="\t")
            GO.columns=["gene_id","go_id","go_name","go_definition"]
            df_dge=pd.merge(df_dge, GO, on=["gene_id"], how="left")
            for c in GO.columns.tolist():
                GO[c]=GO[c].apply(lambda x: fix_go(x) )

            eventlog = UserLogging(email=current_user.email,action="download aarnaseqlake")
            db.session.add(eventlog)
            db.session.commit()

            if plot_arguments["download_format_value"] == "xlsx":
                outfile = io.BytesIO()
                EXC=pd.ExcelWriter(outfile)
                df_dge.to_excel(EXC,sheet_name="dge",index=None)
                EXC.save()
                outfile.seek(0)
                return send_file(outfile, attachment_filename=plot_arguments["download_name"]+ ".dge." + plot_arguments["download_format_value"],as_attachment=True )

            elif plot_arguments["download_format_value"] == "tsv":               
                return Response(df_dge.to_csv(sep="\t"), mimetype="text/csv", headers={"Content-disposition": "attachment; filename=%s.tsv" %(plot_arguments["download_name"]+".dge")})



        if download == "MAplot":
            plot_arguments=session["plot_arguments"]
            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf = get_tables(plot_arguments)

            if type(df_dge) != type(pd.DataFrame()):
                flash("No differential available to perform gene expression for an MA plot.",'error')
                return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])

            reset_info=check_session_app(session,"iscatterplot",apps)
            if reset_info:
                flash(reset_info,'error')

            session["filename"]="<from RNAseq lake>"
            plot_arguments=iscatterplot.figure_defaults()
            session["plot_arguments"]=plot_arguments
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="iscatterplot"

            df_dge["log10(baseMean)"]=df_dge["baseMean"].apply(lambda x: np.log10(x) )
            df_dge.loc[ df_dge["padj"]<=0.05,"Significant"]="yes"
            df_dge.loc[ df_dge["padj"]>0.05,"Significant"]="no"

            df_dge=df_dge.astype(str)
            session["df"]=df_dge.to_json()

            plot_arguments["xcols"]=df_dge.columns.tolist()
            plot_arguments["ycols"]=df_dge.columns.tolist()
            plot_arguments["groups"]=df_dge.columns.tolist()
            plot_arguments["labels_col"]=df_dge.columns.tolist()
            plot_arguments["xvals"]="log10(baseMean)"
            plot_arguments["yvals"]="log2FoldChange"
            plot_arguments["labels_col_value"]="gene_name"
            plot_arguments["groups_value"]="Significant"
            plot_arguments["list_of_groups"]=["yes","no"]

            plot_arguments["title"]="MA plot"
            plot_arguments["xlabel"]="log10(base Mean)"
            plot_arguments["ylabel"]="log2(FC)"

            groups_settings=[]
            group_dic={"name":"yes",\
                "markers":"4",\
                "markersizes_col":"select a column..",\
                "markerc":"red",\
                "markerc_col":"select a column..",\
                "markerc_write":plot_arguments["markerc_write"],\
                "edge_linewidth":plot_arguments["edge_linewidth"],\
                "edge_linewidth_col":"select a column..",\
                "edgecolor":plot_arguments["edgecolor"],\
                "edgecolor_col":"select a column..",\
                "edgecolor_write":"",\
                "marker":"circle",\
                "markerstyles_col":"select a column..",\
                "marker_alpha":"0.25",\
                "markeralpha_col_value":"select a column.."}
            groups_settings.append(group_dic)
            group_dic={"name":"no",\
                "markers":"4",\
                "markersizes_col":"select a column..",\
                "markerc":"black",\
                "markerc_col":"select a column..",\
                "markerc_write":plot_arguments["markerc_write"],\
                "edge_linewidth":plot_arguments["edge_linewidth"],\
                "edge_linewidth_col":"select a column..",\
                "edgecolor":plot_arguments["edgecolor"],\
                "edgecolor_col":"select a column..",\
                "edgecolor_write":"",\
                "marker":"circle",\
                "markerstyles_col":"select a column..",\
                "marker_alpha":"0.25",\
                "markeralpha_col_value":"select a column.."}
            groups_settings.append(group_dic)
            plot_arguments["groups_settings"]=groups_settings

            session["plot_arguments"]=plot_arguments

            return render_template('/apps/iscatterplot.html', filename=session["filename"], apps=apps, **plot_arguments)

        if download == "Volcanoplot":
            plot_arguments=session["plot_arguments"]
            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf = get_tables(plot_arguments)

            if type(df_ge) != type(pd.DataFrame()):
                flash("No differential available to perform gene expression for an MA plot.",'error')
                return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])

            reset_info=check_session_app(session,"iscatterplot",apps)
            if reset_info:
                flash(reset_info,'error')

            session["filename"]="<from RNAseq lake>"
            plot_arguments=iscatterplot.figure_defaults()
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="iscatterplot"

            df_dge["-log10(padj)"]=df_dge["padj"].apply(lambda x: np.log10(x)*-1 )
            df_dge.loc[ df_dge["padj"]<=0.05,"Significant"]="yes"
            df_dge.loc[ df_dge["padj"]>0.05,"Significant"]="no"

            df_dge=df_dge.astype(str)
            session["df"]=df_dge.to_json()

            plot_arguments["xcols"]=df_dge.columns.tolist()
            plot_arguments["ycols"]=df_dge.columns.tolist()
            plot_arguments["groups"]=df_dge.columns.tolist()
            plot_arguments["labels_col"]=df_dge.columns.tolist()
            plot_arguments["xvals"]="log2FoldChange"
            plot_arguments["yvals"]="-log10(padj)"
            plot_arguments["labels_col_value"]="gene_name"
            plot_arguments["groups_value"]="Significant"
            plot_arguments["list_of_groups"]=["yes","no"]

            plot_arguments["title"]="Volcano plot"
            plot_arguments["xlabel"]="log2(FC)"
            plot_arguments["ylabel"]="-log10(padj)"

            groups_settings=[]
            group_dic={"name":"yes",\
                "markers":"4",\
                "markersizes_col":"select a column..",\
                "markerc":"red",\
                "markerc_col":"select a column..",\
                "markerc_write":plot_arguments["markerc_write"],\
                "edge_linewidth":plot_arguments["edge_linewidth"],\
                "edge_linewidth_col":"select a column..",\
                "edgecolor":plot_arguments["edgecolor"],\
                "edgecolor_col":"select a column..",\
                "edgecolor_write":"",\
                "marker":"circle",\
                "markerstyles_col":"select a column..",\
                "marker_alpha":"0.25",\
                "markeralpha_col_value":"select a column.."}
            groups_settings.append(group_dic)
            group_dic={"name":"no",\
                "markers":"4",\
                "markersizes_col":"select a column..",\
                "markerc":"black",\
                "markerc_col":"select a column..",\
                "markerc_write":plot_arguments["markerc_write"],\
                "edge_linewidth":plot_arguments["edge_linewidth"],\
                "edge_linewidth_col":"select a column..",\
                "edgecolor":plot_arguments["edgecolor"],\
                "edgecolor_col":"select a column..",\
                "edgecolor_write":"",\
                "marker":"circle",\
                "markerstyles_col":"select a column..",\
                "marker_alpha":"0.25",\
                "markeralpha_col_value":"select a column.."}
            groups_settings.append(group_dic)
            plot_arguments["groups_settings"]=groups_settings

            session["plot_arguments"]=plot_arguments

            return render_template('/apps/iscatterplot.html', filename=session["filename"], apps=apps, **plot_arguments)

        if download == "iheatmap":


            plot_arguments=session["plot_arguments"]
            plot_arguments, df_metadata, df_dge, df_ge, siggenesdf = get_tables(plot_arguments)
            sig_genes=df_dge[df_dge["padj"]<0.05]["gene_name"].tolist()
            df_ge=df_ge[df_ge["gene_name"].isin(sig_genes)]

            if type(df_ge) != type(pd.DataFrame()):
                flash("No differential available to perform gene expression for an MA plot.",'error')
                return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])

            reset_info=check_session_app(session,"iheatmap",apps)
            if reset_info:
                flash(reset_info,'error')

            plot_arguments=iheatmap.figure_defaults()

            session["filename"]="<from RNAseq lake>"
            session["plot_arguments"]=plot_arguments
            session["COMMIT"]=app.config['COMMIT']
            session["app"]="iheatmap"

            cols=df_ge.columns.tolist()
            df_de=df_ge.astype(str)
            session["df"]=df_ge.to_json()

            plot_arguments["xcols"]=cols
            plot_arguments["ycols"]=cols
            plot_arguments["xvals"]="gene_name"
            available_rows=list(set(df_ge["gene_name"].tolist()))
            available_rows.sort()
            plot_arguments["available_rows"]=available_rows
            plot_arguments["yvals"]=[ s for s in cols if s not in ["gene_name","gene_id"] ]
            plot_arguments["title"]="Heatmap"
            plot_arguments["zscore_value"]="row"
            plot_arguments["colorscale_value"]='bluered'
            plot_arguments["lower_value"]="-2"
            plot_arguments["center_value"]="0"
            plot_arguments["upper_value"]="2"
            plot_arguments["lower_color"]="blue"
            plot_arguments["center_color"]="white"
            plot_arguments["upper_color"]="red"
            plot_arguments["col_cluster"]="off"
            plot_arguments["title_size_value"]="25"
            plot_arguments["color_bar_label"]="z-score"
            plot_arguments["findrowup"]="10"
            plot_arguments["findrowdown"]="10"
            plot_arguments["xticklabels"]="on"

            session["plot_arguments"]=plot_arguments

            return render_template('/apps/iheatmap.html', filename=session["filename"], apps=apps, **plot_arguments)
        
        return render_template('apps/aarnaseqlake.html',  apps=apps, **session["plot_arguments"])
