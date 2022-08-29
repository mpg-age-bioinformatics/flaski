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
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
from pyflaski.scatterplot import make_figure, figure_defaults
import os
import uuid
import traceback
import json
import base64
import pandas as pd
import time
import plotly.express as px
# from plotly.io import write_image
import plotly.graph_objects as go
from werkzeug.utils import secure_filename
from myapp import db
from myapp.models import UserLogging
from time import sleep
import pyflaski as flaski
import sys
import json

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("convert",url_base_pathname=f'{PAGE_PREFIX}/convert/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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

def check_app(file):
    if file.split(".")[-1] not in [ "ses", "arg" ]:
        return None, None, "Not a valid file."
    with open(file, "r") as f:
        session_content=json.load(f)
    return session_content, session_content["app"], None

def scatterplot_import(session_import, last_modified="need a value here"):
    pa=session_import["plot_arguments"]
    pan=flaski.scatterplot.figure_defaults()
    pa_keys=list(pa.keys())
    pan_keys=list(pan.keys())

    maps={'select a column..':None, 'None':None, ".off":None, "off":None, ".on":True, "on":True} 
    maps_keys=list(maps.keys())
    for k in pan_keys:
        if k not in ["show_axis", "tick_axis", "show_legend", "labels_arrows_value", "grid_value" ] :
            if k in pa_keys :
                if pa[k] in maps_keys:
                    pan[k] = maps[ pa[k] ]
                else:
                    pan[k] = pa[k]

    if pa["show_legend"] in [".on" , "on" ]:
        pan["show_legend"]=["show_legend"]
    else:
        pan["show_legend"]=[]

    if pa["labels_arrows_value"] != 'None' :
        pan["labels_arrows_value"]=pa["labels_arrows_value"]
    else:
        pan["labels_arrows_value"]=[]

    if pa["grid_value"] != 'None' :
        pan["grid_value"]=pa["grid_value"]
    else:
        pan["grid_value"]=[]

    show_axis=[]
    for k in [ "left_axis","right_axis","upper_axis","lower_axis"] :
        if pa[k] in [".on", "on" ] :
            show_axis.append(k)
    pan["show_axis"] = show_axis

    tick_axis=[]
    for k in ["tick_x_axis","tick_y_axis"] :
        if pa[k] in [".on", "on" ] :
            tick_axis.append(k)
    pan["tick_axis"] = tick_axis

    df=session_import["df"]
        
    session_data={ "session_data": {"app": { "scatterplot": {"filename":session_import['filename'] ,'last_modified':last_modified,"df":df,"pa":pan} } } }
    session["APP_VERSION"]=app.config['APP_VERSION']
    session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION
    
    return session_data

def david_import(session_import, last_modified="need a value here"):
    pa=session_import["plot_arguments"]
    pan=flaski.david.figure_defaults()
    pa_keys=list(pa.keys())
    pan_keys=list(pan.keys())
    for k in pan_keys:
        if k in pa_keys :
            pan[k] = pa[k]
            
    if pan["ids"] == "Enter target genes here..." :
        pan["ids"]=None
    if "Leave empty if you want to use all annotated genes for your organism" in pan["ids_bg"] :
        pan["ids_bg"]=None  
    if pan["user"] == "" :
        pan["user"]=None
        
    david_df=session_import["david_df"]
    report_stats=session_import["report_stats"]
    
    session_data={ "session_data": {"app": { "david": {"filename":session_import["filename"],'last_modified':last_modified,"pa":pan} } } }
    session_data["APP_VERSION"]=app.config['APP_VERSION']
    session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION
    return session_data, david_df, report_stats

def cellplot_import(session_import,last_modified="need a value here"):
    pa=session_import["plot_arguments"]
    pan=flaski.cellplot.figure_defaults()
    pa_keys=list(pa.keys())
    pan_keys=list(pan.keys())

    maps_off={".off":None, "off":None, "":None, "none":None}
    maps_on=[".on","on"]
    for k in pan_keys:
        if k not in ["log10transform", "reverse_color_scale", "write_n_terms", "reverse_y_order", \
                     "xaxis_line", "topxaxis_line", "yaxis_line", "rightyaxis_line" , "grid" ] :
            if k in pa_keys :
                if pa[k] in list( maps_off.keys() ) :
                    pan[k] = maps_off[ pa[k] ]
                if pa[k] in maps_on :
                    pan[k] = None
                else:
                    pan[k] = pa[k]
                    
    df=session_import["df"]
    df_ge=session_import["ge_df"]
    
    session_data={ "session_data": {"app": { "cellplot": {"filename":session_import["filename"] ,'last_modified':last_modified,"df":df,"pa":pan, 'filename2':session_import["ge_filename"], "df_ge": df_ge} } } }
    session_data["APP_VERSION"]=app.config['APP_VERSION']
    session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION
    return session_data


dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-right":"2px"}
card_label_style_={"margin-left":"5px","margin-right":"2px"}

card_input_style={"height":"35px","width":"100%"}
# card_input_style_={"height":"35px","width":"100%","margin-right":"10px"}
card_body_style={ "padding":"2px", "padding-top":"2px"}#,"margin":"0px"}
# card_body_style={ "padding":"2px", "padding-top":"4px","padding-left":"18px"}


@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    eventlog = UserLogging(email=current_user.email, action="visit vcheck")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Version check",current_user),
            html.Div(id="app-content"),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

@dashapp.callback( 
    Output('app-content', 'children'),
    Input('url', 'pathname'))
def make_app_content(pathname):

    app_content=dbc.Row( 
        [
            dbc.Col( 
                [ 
                    dbc.Card(
                        dbc.Form(
                            [ 
                                dcc.Upload(
                                    id='upload-data',
                                    children=html.Div(
                                        [ html.A('drop a file here',id='upload-data-text') ],
                                        style={ 'textAlign': 'center', "padding-top": 35, "margin-bottom": 4,  }
                                    ),
                                    style={
                                        'width': '100%',
                                        'borderWidth': '1px',
                                        'borderStyle': 'dashed',
                                        'borderRadius': '0px',
                                        "margin-bottom": "0px",
                                        'max-width':"375px",
                                        'min-height':"100px",
                                        # "verticalAlign":"center"
                                    },
                                    multiple=False,
                                ),
                                html.Div( id="app-version"), 
                            ]
                        ),
                        body=True,
                        outline=False,
                        color="white",
                    ),
                ],
                sm=9,md=6, lg=5, xl=5, 
                align="center",
                style={ "margin-left":0, "margin-right":0 ,'margin-bottom':"50px",'max-width':"375px"}
            ),
        ],
        align="center",
        justify="center",
        style={"min-height": "86vh", 'verticalAlign': 'center'},
        dcc.Download( id="download-file1" ),
        dcc.Download( id="download-file2" ),
    ) 

    return app_content

@dashapp.callback( 
    Output('upload-data', 'children'),
    Output("download-file1","data"),
    Output("download-file2","data"),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename,last_modified,session_id):
    if not filename :
        raise dash.exceptions.PreventUpdate
    # try:
        # app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "scatterplot")
    content_type, content_string = contents.split(',')
    decoded=base64.b64decode(content_string)
    decoded=decoded.decode('utf-8')
    session=json.loads(decoded)


    ## make conversions here



    FLASKI_version=session["APP_VERSION"]
    PYFLASKI_version=session["PYFLASKI_VERSION"]
    APP=list(session["session_data"]["app"].keys())[0]

    message=dcc.Markdown(f"**Session info**\
        \n\n\
         Flaski: {FLASKI_version}\
        \n\
        pyflaski: {PYFLASKI_version}\
        \n\
        App: {APP}")

    children=html.Div(
        [ html.A(message,id='upload-data-text') ],
        style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
    )        
    return children, None, None

    # except:
    #     children=html.Div(
    #         [ html.A("! file could not be read !",id='upload-data-text') ],
    #         style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
    #     )
    #     return  children


@dashapp.callback(
    Output( { 'type': 'collapse-toast-traceback', 'index': MATCH }, "is_open"),
    Output( { 'type': 'toggler-toast-traceback', 'index': MATCH }, "children"),
    Input( { 'type': 'toggler-toast-traceback', 'index': MATCH }, "n_clicks"),
    State( { 'type': 'collapse-toast-traceback', 'index': MATCH }, "is_open"),
    prevent_initial_call=True
)
def toggle_toast_traceback(n,is_open):
    if not is_open:
        return not is_open , "collapse"
    else:
        return not is_open , "expand"

@dashapp.callback(
    Output( { 'type': 'toast-error', 'index': ALL }, "is_open" ),
    Output( 'toast-email' , "children" ),
    Output( { 'type': 'toast-error', 'index': ALL }, "n_clicks" ),
    Input( { 'type': 'help-toast-traceback', 'index': ALL }, "n_clicks" ),
    State({ "type":"traceback", "index":ALL }, "data"),
    State( "session-data", "data"),
    prevent_initial_call=True
)
def help_email(n,tb_str, session_data):
    closed=[ False for s in n ]
    n=[ s for s in n if s ]
    clicks=[ 0 for s in n ]
    n=[ s for s in n if s > 0 ]
    if n : 

        toast=dbc.Toast(
            [
                "We have received your request for help and will get back to you as soon as possible.",
            ],
            id={'type':'success-email','index':"email"},
            header="Help",
            is_open=True,
            dismissable=True,
            icon="success",
        )

        if tb_str :
            tb_str= [ s for s in tb_str if s ]
            tb_str="\n\n***********************************\n\n".join(tb_str)
        else:
            tb_str="! traceback could not be found"

        ask_for_help(tb_str,current_user, "vcheck", session_data)

        return closed, toast, clicks
    else:
        
        raise PreventUpdate

@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open