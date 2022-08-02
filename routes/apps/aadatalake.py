from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, make_table, encode_session_app
import os
import uuid
# import traceback
import json
import base64
import pandas as pd
# import time
from werkzeug.utils import secure_filename
import humanize
from myapp.models import User
import stat
from datetime import datetime
# import dash_table
import shutil
from time import sleep
from myapp import db
from myapp.models import UserLogging
from ._aadatalake import read_results_files, read_gene_expression, read_genes, read_significant_genes, \
    filter_samples, filter_genes, filter_gene_expression, nFormat, read_dge,\
        make_volcano_plot, make_ma_plot, make_pca_plot, make_annotated_col, make_bar_plot, plot_height


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("aadatalake",url_base_pathname=f'{PAGE_PREFIX}/aadatalake/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

if app.config["SESSION_TYPE"] == "sqlalchemy":
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"] , echo=True)
    app.config["SESSION_SQLALCHEMY"] = engine
elif app.config["CACHE_TYPE"] == "RedisCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
    })
elif app.config["CACHE_TYPE"] == "RedisSentinelCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [ 
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), os.environ.get('CACHE_REDIS_SENTINELS_port') ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })

def change_table_minWidth(tb,minwidth):
    st=tb.style_table
    st["minWidth"]=minwidth
    tb.style_table=st
    return tb

def change_fig_minWidth(fig,minwidth):
    st=fig.style
    st["minWidth"]=minwidth
    fig.style=st
    return fig

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=False ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-top":"5px"}
card_input_style={"width":"100%","height":"35px"}
card_body_style={ "padding":"2px", "padding-top":"4px"}


@dashapp.callback(
    Output('protected-content', 'children'),
    Input('session-id', 'data')
    )
def make_layout(session_id):

    ## check if user is authorized
    eventlog = UserLogging(email=current_user.email, action="visit aadatalake")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Data lake",current_user),
            # html.Div(id="app-content"),
            html.Div(id="app_access"),
            html.Div(id="redirect-pca"),
            html.Div(id="redirect-volcano"),
            html.Div(id="redirect-ma"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),
            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dcc.Loading(
                                [
                                    dbc.Card(
                                        [
                                            html.H5("Filters", style={"margin-top":10}), 
                                            html.Label('Data sets'), dcc.Dropdown( id='opt-datasets', multi=True),
                                            html.Label('Groups',style={"margin-top":10}), dcc.Dropdown( id='opt-groups', multi=True),
                                            html.Label('Samples',style={"margin-top":10}), dcc.Dropdown( id='opt-samples', multi=True),
                                            html.Label('Gene names',style={"margin-top":10}), dcc.Dropdown( id='opt-genenames', multi=True),
                                            html.Label('Gene IDs',style={"margin-top":10}), dcc.Dropdown( id='opt-geneids', multi=True),
                                            html.Label('Download file prefix',style={"margin-top":10}), 
                                            dcc.Input(id='download_name', value="data.lake", type='text',style={"width":"100%", "height":"34px"})
                                        ],
                                        body=True
                                    ),
                                    dbc.Button(
                                        'Submit',
                                        id='submit-button-state', 
                                        color="secondary",
                                        n_clicks=0, 
                                        style={"width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
                                    )
                                ],
                                id="loading-output",
                                type="default",
                                style={"margin-top":"50%","height": "100%"} 
                            )
                        ],
                        sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","height": "100%",'overflow': 'scroll'} 
                    ),               
                    dbc.Col( 
                        dcc.Loading(
                            id="loading-output-2",
                            type="default",
                            children=[ html.Div(id="my-output")],
                            style={"margin-top":"50%","height": "100%"} 
                        ),
                        # sm=12,md=6,lg=8,xl=9,#md=9, 
                        style={"height": "100%","width": "100%",'overflow': 'scroll'})
                ],
                align="start",
                justify="left",
                className="g-0",
                style={"height":"86vh","width":"100%","overflow":"scroll"}
                # style={"height":"86vh","width":"100%","overflow":"scroll"}#style={"min-height": "87vh"}
            ),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

## all callback elements with `State` will be updated only once submit is pressed
## all callback elements wiht `Input` will be updated everytime the value gets changed 
@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, datasets, groups, samples, genenames, geneids, download_name):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    
    ## samples
    results_files=selected_results_files[["Set","Group","Reps"]]
    results_files.columns=["Set","Group","Sample"]
    results_files=results_files.drop_duplicates()      
    results_files_=make_table(results_files,"results_files")
    # results_files_ = dbc.Table.from_dataframe(results_files, striped=True, bordered=True, hover=True)
    download_samples=html.Div( 
        [
            html.Button(id='btn-samples', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-samples")
        ]
    )

    ## gene expression
    if datasets or groups or samples or  genenames or  geneids :
        print("1 -- gene expression")
        gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)
        
        gene_expression_=make_table(gene_expression,"gene_expression")#,fixed_columns={'headers': True, 'data': 2} )
        # gene_expression_ = dbc.Table.from_dataframe(gene_expression, striped=True, bordered=True, hover=True)
        download_geneexp=html.Div( 
            [
                html.Button(id='btn-geneexp', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                dcc.Download(id="download-geneexp")
            ]
        )
        gene_expression_bol=True
    else:
        gene_expression_bol=False

    ## barPlot
    selected_sets=list(set(results_files["Set"]))
    if (genenames and len(genenames) == 1) or (geneids and len(geneids) == 1):
        print("2 -- bar plot")

        gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)
        
        bar_df=gene_expression
        if genenames:
            label=genenames[0]
        elif geneids:
            label=geneids[0]

        plot_height_=plot_height(selected_sets)
        
        bar_plot=make_bar_plot(bar_df, ["gene_name", "gene_id"], selected_sets, label)
        bar_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".bar" }}
        bar_plot=dcc.Graph(figure=bar_plot, config=bar_config, style={"width":"100%","overflow-x":"auto", "height":plot_height_}, id="bar_plot")
 
        # download_bar=html.Div( 
        # [   
        #     html.Button(id='btn-download-bar', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
        #     dcc.Download(id="download-bar")
        # ])      
        gene_expression_bar_bol=True
    else:
        gene_expression_bar_bol=False

    ## PCA
    selected_sets=list(set(selected_results_files["Set"]))
    if len(selected_sets) == 1 : 
        print("3 -- PCA")
        pca_data=filter_gene_expression(ids2labels,None,None,cache)
        pca_plot, pca_pa, pca_df=make_pca_plot(pca_data,selected_sets[0])
        pca_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".pca" }}
        pca_plot=dcc.Graph(figure=pca_plot, config=pca_config, style={"width":"100%","overflow-x":"auto"})
        
        iscatter_pca=html.Div( 
        [
            html.Button(id='btn-iscatter_pca', n_clicks=0, children='Scatterplot', 
            style={"margin-top":4, \
                "margin-left":4,\
                "margin-right":4,\
                'background-color': "#5474d8", \
                "color":"white"})
        ])
                
        pca_bol=True
    else:
        pca_bol=False
    
    ## differential gene expression
    dge_bol=False
    volcano_plot=None
    if not samples:
        print("4 -- DGE")
        if len(selected_sets) == 1 :
            dge_groups=list(set(selected_results_files["Group"]))
            if len(dge_groups) == 2:
                dge=read_dge(selected_sets[0], dge_groups, cache)
                dge_plots=dge.copy()
                if genenames:
                    dge=dge[dge["gene name"].isin(genenames)]                    
                if geneids:
                    dge=dge[dge["gene id"].isin(geneids)]

                dge_=make_table(dge,"dge")
                download_dge=html.Div( 
                                [
                                    html.Button(id='btn-dge', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                                    dcc.Download(id="download-dge")
                                ]
                            )

                annotate_genes=[]
                if genenames:
                    genenames_=dge[dge["gene name"].isin(genenames)]["gene name"].tolist()
                    annotate_genes=annotate_genes+genenames_
                if geneids:
                    genenames_=dge[dge["gene id"].isin(geneids)]["gene name"].tolist()
                    annotate_genes=annotate_genes+genenames_                

                volcano_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".volcano" }}
                volcano_plot, volcano_pa, volcano_df=make_volcano_plot(dge_plots, selected_sets[0], annotate_genes)
                volcano_plot.update_layout(clickmode='event+select')
                volcano_plot=dcc.Graph(figure=volcano_plot, config=volcano_config, style={"width":"100%","overflow-x":"auto"}, id="volcano_plot")                

                iscatter_volcano=html.Div( 
                [
                    html.Button(id='btn-iscatter_volcano', n_clicks=0, children='Scatterplot', 
                    style={"margin-top":4, \
                        "margin-left":4,\
                        "margin-right":4,\
                        'background-color': "#5474d8", \
                        "color":"white"})
                ])

                ma_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".ma" }}
                ma_plot, ma_pa, ma_df=make_ma_plot(dge_plots, selected_sets[0],annotate_genes )
                ma_plot.update_layout(clickmode='event+select')
                ma_plot=dcc.Graph(figure=ma_plot, config=ma_config, style={"width":"100%","overflow-x":"auto"}, id="ma_plot")

                iscatter_ma=html.Div( 
                [
                    html.Button(id='btn-iscatter_ma', n_clicks=0, children='Scatterplot', 
                    style={"margin-top":4, \
                        "margin-left":4,\
                        "margin-right":4,\
                        'background-color': "#5474d8", \
                        "color":"white"})
                ])

                if genenames or geneids:
                    if len(genenames) == 1 or len(geneids) == 1:
                        bar_df=dge.copy()
                        
                        cols_exclude=["gene id", "gene name","base Mean","log2 FC","lfc SE","p value","padj"]

                        if genenames:
                            label=genenames[0]
                        elif geneids:
                            label=geneids[0]

                        
                        plot_height_=plot_height(selected_sets)

                        bar_plot=make_bar_plot(bar_df, cols_exclude, selected_sets, label)
                        bar_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".bar" }}
                        bar_plot=dcc.Graph(figure=bar_plot, config=bar_config, style={"width":"100%","overflow-x":"auto", "height":plot_height_}, id="bar_plot")
                        
                        # download_bar=html.Div( 
                        # [   
                        #     html.Button(id='btn-download-bar', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                        #     dcc.Download(id="download-bar")
                        # ])      
                        gene_expression_bar_bol=True

                dge_bol=True

    if  ( dge_bol ) & ( pca_bol ) & (gene_expression_bar_bol) :
        print("5 -- dge, pca, bar plot" )
        minwidth=["Samples","Expression", "PCA", "Bar Plot", "DGE","Volcano","MA"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)
        dge_=change_table_minWidth(dge_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)
        bar_plot_=change_fig_minWidth(bar_plot,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ pca_plot, iscatter_pca ], 
                    label="PCA", id="tab-pca", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),        
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dge_, download_dge], 
                    label="DGE", id="tab-dge", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dbc.Row( [
                             dbc.Col(volcano_plot), 
                             dbc.Col( [ html.Div(id="volcano-plot-table") ]   
                             ) ], 
                             style={"minWidth":minwidth}),
                    dbc.Row([iscatter_volcano,html.Div(id="volcano-bt")]),
                    ], 
                    label="Volcano", id="tab-volcano", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dbc.Row( [
                             dbc.Col(ma_plot), 
                             dbc.Col( [ html.Div(id="ma-plot-table") ]   
                             ) ], 
                             style={"minWidth":minwidth}),
                    dbc.Row([iscatter_ma,html.Div(id="ma-bt")]),
                    ] ,
                    label="MA", id="tab-ma", 
                    style={"margin-top":"0%"})
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )


    elif  ( dge_bol ) & ( pca_bol ) :
        print("6 -- dge, pca")

        minwidth=["Samples","Expression", "PCA", "DGE","Volcano","MA"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)
        dge_=change_table_minWidth(dge_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ pca_plot, iscatter_pca ], 
                    label="PCA", id="tab-pca", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dge_, download_dge], 
                    label="DGE", id="tab-dge", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dbc.Row( [
                             dbc.Col(volcano_plot), 
                             dbc.Col( [ html.Div(id="volcano-plot-table") ]   
                             ) ], 
                             style={"minWidth":minwidth}),
                    dbc.Row([iscatter_volcano,html.Div(id="volcano-bt")]),
                    ], 
                    label="Volcano", id="tab-volcano", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dbc.Row( [
                             dbc.Col(ma_plot), 
                             dbc.Col( [ html.Div(id="ma-plot-table") ]   
                             ) ], 
                             style={"minWidth":minwidth}),
                    dbc.Row([iscatter_ma,html.Div(id="ma-bt")]),
                    ] ,
                    label="MA", id="tab-ma", 
                    style={"margin-top":"0%"})
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif  (pca_bol) & (gene_expression_bar_bol) :
        print("7 -- pca, barplot")

        minwidth=["Samples","Expression", "PCA", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)
        bar_plot_=change_fig_minWidth(bar_plot,minwidth)

        out=dcc.Tabs( [ 
                    dcc.Tab([ results_files_, download_samples], 
                            label="Samples", id="tab-samples",
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ pca_plot, iscatter_pca ], 
                            label="PCA", id="tab-pca", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),
                    dcc.Tab( [ gene_expression_, download_geneexp], 
                            label="Expression", id="tab-geneexpression", 
                            style={"margin-top":"0%"}),
                    ],
                    mobile_breakpoint=0,
                    style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )


    elif (gene_expression_bol) & (gene_expression_bar_bol) :
        print("8 -- ge, bar plot")
        minwidth=["Samples","Expression", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)
        bar_plot_=change_fig_minWidth(bar_plot,minwidth)


        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
             dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif  pca_bol :
        print("9 -- pca")

        minwidth=["Samples","Expression", "PCA"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)

        out=dcc.Tabs( [ 
                    dcc.Tab([ results_files_, download_samples], 
                            label="Samples", id="tab-samples",
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ pca_plot, iscatter_pca ], 
                            label="PCA", id="tab-pca", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ gene_expression_, download_geneexp], 
                            label="Expression", id="tab-geneexpression", 
                            style={"margin-top":"0%"}),
                    ],  
                    mobile_breakpoint=0,
                    style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
    
    elif gene_expression_bar_bol :
        print("10 -- bar plot")

        minwidth=["Samples","Expression", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        bar_plot_=change_fig_minWidth(bar_plot,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
             dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif gene_expression_bol:
        print("11 -- ge")

        minwidth=["Samples","Expression"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    else:
        print("12 -- else")
        minwidth=["Samples"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        # results_files_=change_table_minWidth(results_files_,minwidth)

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_, 
                        download_samples
                    ], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
    return out

@dashapp.callback( 
    Output('volcano-plot-table', 'children'),
    Output('volcano-bt', 'children'),
    Input('volcano_plot', 'selectedData') 
)
def display_volcano_data(selectedData):
    if selectedData:
        selected_genes=selectedData["points"]
        selected_genes=[ s["text"] for s in selected_genes ]
        df=pd.DataFrame({"Selected genes":selected_genes})
        df=make_table(df,"selected_volcano")
        st=df.style_table
        st["width"]="50%"
        st["margin-top"]="40px"
        st["align"]="center"
        st["margin-left"]="auto"
        st["margin-right"]="auto"
        df.style_table=st
        df.style_cell={'whiteSpace': 'normal', 'textAlign': 'center'}

        download_selected_volcano=html.Div( 
                [
                    html.Button(id='btn-selected_volcano', n_clicks=0, children='Excel', 
                    style={"margin-top":4, \
                        "margin-left":4,\
                        "margin-right":4,\
                        'background-color': "#5474d8", \
                        "color":"white"}),
                    dcc.Download(id="download-selected_volcano")
                ])

        return df, download_selected_volcano
    else:
        return None, None
    
@dashapp.callback(
    Output("download-selected_volcano", "data"),
    Input("btn-selected_volcano", "n_clicks"),
    State('volcano_plot', 'selectedData'),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_selected_volcano(n_clicks,selectedData,datasets,groups,download_name):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=None, cache=cache)    
    selected_genes=selectedData["points"]
    selected_genes=[ s["text"] for s in selected_genes ]
    dge_datasets=list(set(selected_results_files["Set"]))
    dge_groups=list(set(selected_results_files["Group"]))
    dge=read_dge(dge_datasets[0], dge_groups, cache)
    dge=dge[dge["gene name"].isin(selected_genes)]                    
    fileprefix=secure_filename(str(download_name))
    filename="%s.dge.volcano_selected.xlsx" %fileprefix
    return dcc.send_data_frame(dge.to_excel, filename, sheet_name="dge.volcano", index=False)

@dashapp.callback(
    Output("redirect-volcano", 'children'),
    Input("btn-iscatter_volcano", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    prevent_initial_call=True,
)
def volcano_to_iscatterplot(n_clicks,datasets, groups, genenames, geneids):
    if n_clicks:
        selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=None, cache=cache)    
        dge_datasets=list(set(selected_results_files["Set"]))
        dge_groups=list(set(selected_results_files["Group"]))
        dge=read_dge(dge_datasets[0], dge_groups, cache)
        annotate_genes=[]
        if genenames:
            genenames_=dge[dge["gene name"].isin(genenames)]["gene name"].tolist()
            annotate_genes=annotate_genes+genenames_
        if geneids:
            genenames_=dge[dge["gene id"].isin(geneids)]["gene name"].tolist()
            annotate_genes=annotate_genes+genenames_     
        volcano_plot, volcano_pa, volcano_df=make_volcano_plot(dge, dge_datasets[0], annotate_genes)
        # reset_info=check_session_app(session,"iscatterplot",current_user.user_apps)

        volcano_pa["xcols"]=volcano_df.columns.tolist()
        volcano_pa["ycols"]=volcano_df.columns.tolist()
        volcano_pa["groups"]=["None"]+volcano_df.columns.tolist()
        
        volcano_df["datalake_search"]=volcano_df["gene name"].apply(lambda x: make_annotated_col(x, annotate_genes) )
        volcano_pa["labels_col"]=["select a column.."]+volcano_df.columns.tolist()
        # volcano_pa["labels_col"]=["select a column.."]+volcano_df.columns.tolist()
        # volcano_pa["labels_col_value"]="select a column.."
        volcano_df=volcano_df.drop(["___label___"],axis=1)

        # ession_data={ "session_data": {"app": { "scatterplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        # session_data["APP_VERSION"]=app.config['APP_VERSION']

        session_data={ "APP_VERSION": app.config['APP_VERSION'],
            "session_data": 
                {
                    "app": 
                    {
                        "scatterplot": 
                        {
                            "df": volcano_df.to_json() ,
                            "filename": "from.datalake.json", 
                            "last_modified": datetime.now().timestamp(), 
                            "pa": volcano_pa
                        }
                    }
                }
            }
                        
        session_data=encode_session_app(session_data)
        session["session_data"]=session_data
        from time import sleep
        sleep(2)

        # session["filename"]="<from RNAseq lake>"
        # session["plot_arguments"]=volcano_pa
        # session["COMMIT"]=app.config['COMMIT']
        # session["app"]="iscatterplot"
        # session["df"]=volcano_df.to_json()

        return dcc.Location(pathname=f"{PAGE_PREFIX}/scatterplot/", id="index")

@dashapp.callback( 
    Output('ma-plot-table', 'children'),
    Output('ma-bt', 'children'),
    Input('ma_plot', 'selectedData') 
)
def display_ma_data(selectedData):
    if selectedData:
        selected_genes=selectedData["points"]
        selected_genes=[ s["text"] for s in selected_genes ]
        df=pd.DataFrame({"Selected genes":selected_genes})
        df=make_table(df,"selected_ma")
        st=df.style_table
        st["width"]="50%"
        st["margin-top"]="40px"
        st["align"]="center"
        st["margin-left"]="auto"
        st["margin-right"]="auto"
        df.style_table=st
        df.style_cell={'whiteSpace': 'normal', 'textAlign': 'center'}

        download_selected_ma=html.Div( 
                [
                    html.Button(id='btn-selected_ma', n_clicks=0, children='Excel', 
                    style={"margin-top":4, \
                        "margin-left":4,\
                        "margin-right":4,\
                        'background-color': "#5474d8", \
                        "color":"white"}),
                    dcc.Download(id="download-selected_ma")
                ])

        return df, download_selected_ma
    else:
        return None, None

@dashapp.callback(
    Output("download-selected_ma", "data"),
    Input("btn-selected_ma", "n_clicks"),
    State('ma_plot', 'selectedData'),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_selected_ma(n_clicks,selectedData,datasets,groups,download_name):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=None, cache=cache)    
    selected_genes=selectedData["points"]
    selected_genes=[ s["text"] for s in selected_genes ]
    dge_datasets=list(set(selected_results_files["Set"]))
    dge_groups=list(set(selected_results_files["Group"]))
    dge=read_dge(dge_datasets[0], dge_groups, cache)
    dge=dge[dge["gene name"].isin(selected_genes)]                    
    fileprefix=secure_filename(str(download_name))
    filename="%s.dge.ma_selected.xlsx" %fileprefix
    return dcc.send_data_frame(dge.to_excel, filename, sheet_name="dge.ma", index=False)

@dashapp.callback(
    Output("redirect-ma", 'children'),
    Input("btn-iscatter_ma", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    prevent_initial_call=True,
)
def ma_to_iscatterplot(n_clicks,datasets, groups, genenames, geneids):
    if n_clicks:
        selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=None, cache=cache)    
        dge_datasets=list(set(selected_results_files["Set"]))
        dge_groups=list(set(selected_results_files["Group"]))
        dge=read_dge(dge_datasets[0], dge_groups, cache)
        annotate_genes=[]
        if genenames:
            genenames_=dge[dge["gene name"].isin(genenames)]["gene name"].tolist()
            annotate_genes=annotate_genes+genenames_
        if geneids:
            genenames_=dge[dge["gene id"].isin(geneids)]["gene name"].tolist()
            annotate_genes=annotate_genes+genenames_     
        ma_plot, ma_pa, ma_df=make_ma_plot(dge, dge_datasets[0],annotate_genes )
        # reset_info=check_session_app(session,"iscatterplot",current_user.user_apps)

        ma_pa["xcols"]=ma_df.columns.tolist()
        ma_pa["ycols"]=ma_df.columns.tolist()
        ma_pa["groups"]=["None"]+ma_df.columns.tolist()

        ma_df["datalake_search"]=ma_df["gene name"].apply(lambda x:  make_annotated_col(x, annotate_genes) )
        ma_df=ma_df.drop(["___label___"],axis=1)
        ma_pa["labels_col"]=["select a column.."]+ma_df.columns.tolist()
        ma_pa["labels_col_value"]="select a column.."

        session["filename"]="<from RNAseq lake>"
        session["plot_arguments"]=ma_pa
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="iscatterplot"

        session["df"]=ma_df.to_json()
        return dcc.Location(pathname="/scatterplot", id="index")

@dashapp.callback(
    Output("redirect-pca", 'children'),
    Input("btn-iscatter_pca", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    prevent_initial_call=True,
)
def pca_to_iscatterplot(n_clicks,datasets, groups):
    if n_clicks:
        selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=None, cache=cache)    
        pca_data=filter_gene_expression(ids2labels,None,None,cache)
        selected_sets=list(set(selected_results_files["Set"]))
        pca_plot, pca_pa, pca_df=make_pca_plot(pca_data,selected_sets[0])
        # reset_info=check_session_app(session,"iscatterplot",current_user.user_apps)

        pca_pa["xcols"]=pca_df.columns.tolist()
        pca_pa["ycols"]=pca_df.columns.tolist()
        pca_pa["groups"]=["None"]+pca_df.columns.tolist()
        pca_pa["labels_col"]=["select a column.."]+pca_df.columns.tolist()
        pca_pa["labels_col_value"]="select a column.."

        session["filename"]="<from RNAseq lake>"
        session["plot_arguments"]=pca_pa
        session["COMMIT"]=app.config['COMMIT']
        session["app"]="iscatterplot"

        session["df"]=pca_df.to_json()
        return dcc.Location(pathname="/scatterplot", id="index")

@dashapp.callback(
    Output("download-samples", "data"),
    Input("btn-samples", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_samples(n_clicks,datasets, groups, samples, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    results_files=selected_results_files[["Set","Group","Reps"]]
    results_files.columns=["Set","Group","Sample"]
    results_files=results_files.drop_duplicates()
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.samples.xlsx" %fileprefix
    return dcc.send_data_frame(results_files.to_excel, filename, sheet_name="samples", index=False)

@dashapp.callback(
    Output("download-geneexp", "data"),
    Input("btn-geneexp", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_geneexp(n_clicks,datasets, groups, samples, genenames, geneids, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.gene_expression.xlsx" %fileprefix
    return dcc.send_data_frame(gene_expression.to_excel, filename, sheet_name="gene exp.", index=False)

@dashapp.callback(
    Output("download-dge", "data"),
    Input("btn-dge", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_dge(n_clicks,datasets, groups, samples, genenames, geneids, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    # gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)

    if not samples:
        dge_datasets=list(set(selected_results_files["Set"]))
        if len(dge_datasets) == 1 :
            dge_groups=list(set(selected_results_files["Group"]))
            if len(dge_groups) == 2:
                dge=read_dge(dge_datasets[0], dge_groups, cache)
                if genenames:
                    dge=dge[dge["gene name"].isin(genenames)]                    
                if geneids:
                    dge=dge[dge["gene id"].isin(geneids)]
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.dge.xlsx" %fileprefix
    return dcc.send_data_frame(dge.to_excel, filename, sheet_name="dge", index=False)

# @dashapp.callback(
#     Output('download-bar', 'data'),
#     Input('btn-download-bar',"n_clicks"),
#     State('bar_plot', 'figure'),
#     State("opt-datasets", "value"),
#     State("opt-groups", "value"),
#     State("opt-samples", "value"),
#     State("download_name", "value"),
#     prevent_initial_call=True,
# )
# def download_bar(n_clicks,figure,datasets, groups, samples,download_name):
#     selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
#     ## samples
#     results_files=selected_results_files[["Set","Group","Reps"]]
#     results_files.columns=["Set","Group","Sample"]
#     results_files=results_files.drop_duplicates()
#     selected_sets=list(set(results_files["Set"]))

#     minheight=plot_height(selected_sets)

#     fileprefix=secure_filename(str(download_name))
#     pdf_filename="%s.geneExp.bar.Plot.pdf" %fileprefix
    
#     if not pdf_filename:
#         pdf_filename="geneExp.bar.Plot.pdf"
#     pdf_filename=secure_filename(pdf_filename)
#     if pdf_filename.split(".")[-1] != "pdf":
#         pdf_filename=f'{pdf_filename}.pdf'

#     def write_image(figure, graph=figure):
#         fig=go.Figure(graph)
#         fig.write_image(figure, format="pdf", height=minheight, width=minheight)
        
#     return dcc.send_bytes(write_image, pdf_filename)
    

@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Output(component_id='opt-genenames', component_property='options'),
    Output(component_id='opt-geneids', component_property='options'),
    Input('session-id', 'data')
    )
def update_datasets(session_id):
    results_files=read_results_files(cache)
    datasets=list(set(results_files["Set"]))
    datasets=make_options(datasets)

    genes=read_genes(cache)

    genenames=list(set(genes["gene_name"]))
    genenames=make_options(genenames)

    geneids=list(set(genes["gene_id"]))
    geneids=make_options(geneids)

    return datasets, genenames, geneids

@dashapp.callback(
    Output(component_id='opt-groups', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value') )
def update_groups(session_id, datasets):
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)    
    groups_=list(set(selected_results_files["Group"]))
    groups_=make_options(groups_)
    return groups_

@dashapp.callback(
    Output(component_id='opt-samples', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value'),
    Input('opt-groups', 'value') )
def update_reps(session_id, datasets, groups):
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)    
    groups_=list(set(selected_results_files["Group"]))
    groups_=make_options(groups_)

    selected_results_files, ids2labels=filter_samples(datasets=datasets, groups=groups,cache=cache)    
    reps_=list(set(selected_results_files["Reps"]))
    reps_=make_options(reps_)

    return reps_

@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
