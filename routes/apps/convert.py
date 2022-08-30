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
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, check_app, scatterplot_import, david_import, cellplot_import
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

# import pyflaski as flaski
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
            make_navbar_logged("v2 to v3 converter",current_user),
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
            dcc.Download( id="download-file1" ),
            dcc.Download( id="download-file2" ),
        ],
        align="center",
        justify="center",
        style={"min-height": "86vh", 'verticalAlign': 'center'},
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
    filename=secure_filename( filename )
    if not filename :
        raise dash.exceptions.PreventUpdate
    message=dcc.Markdown(f"Not a valid session file.")
    children=html.Div(
        [ html.A(message,id='upload-data-text') ],
        style={ 'textAlign': 'center', "margin-top": 35, "margin-bottom": 4}
    )   
    if filename.split(".")[-1] not in [ "ses"]:#, "arg" ]:     
        return children, None, None

    filename=filename.replace(".ses", ".json").replace(".arg",".json")

    content_type, content_string = contents.split(',')
    decoded=base64.b64decode(content_string)
    decoded=decoded.decode('utf-8')
    session_data=json.loads(decoded)

    # print(session_data.keys())

    session_app=session_data["app"]

    # print(session_app)

    if session_app == "iscatterplot" :
        session_data=scatterplot_import(session_data, last_modified=last_modified)
    
        def write_json(filename,session_data=session_data):
            filename.write(json.dumps(session_data).encode())

        return dash.no_update,  dcc.send_bytes(write_json, filename), dash.no_update
    elif session_app == "david" :
        session_data, david_df, report_stats = david_import(session_data, last_modified=last_modified)

        david_df=pd.read_json(david_df)
        report_stats=pd.read_json(report_stats)

        import io
        output = io.BytesIO()
        writer= pd.ExcelWriter(output)
        david_df.to_excel(writer, sheet_name = 'david', index = None)
        report_stats.to_excel(writer, sheet_name = 'stats', index = None)
        writer.save()
        data=output.getvalue()
        excel_filename=filename.replace(".json", ".xlsx")

        def write_json(filename,session_data=session_data):
            filename.write(json.dumps(session_data).encode())

        return dash.no_update,  dcc.send_bytes(write_json, filename), dcc.send_bytes(data, excel_filename)

    elif session_app == "icellplot" :
        session_data = cellplot_import(session_data, last_modified=last_modified)
    
        def write_json(filename,session_data=session_data):
            filename.write(json.dumps(session_data).encode())

        return dash.no_update,  dcc.send_bytes(write_json, filename), dash.no_update

    else:
        return children, dash.no_update, dash.no_update

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