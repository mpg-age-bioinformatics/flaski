from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_options, GROUPS, GROUPS_INITALS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import json
import base64
import pandas as pd
import zipfile

from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("agebot",url_base_pathname=f'{PAGE_PREFIX}/agebot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="AGE bot",  assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/") update_title='Load...', 

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

# improve tables styling
style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    eventlog = UserLogging(email=current_user.email, action="visit agebot")
    db.session.add(eventlog)
    db.session.commit()

    protected_content=html.Div(
        [
            make_navbar_logged("AGE bot",current_user),
            dbc.Row( html.Div(id="input-field", style={"height":"100%","overflow":"scroll"}) ),
            dbc.Row( dcc.Loading(id="loading-stored-file", children=dcc.Store( id='session-data' )), style={"margin-top":25, "margin-bottom":10} ),
            dbc.Row( html.Div(id="output-field", style={"height":"100%","overflow":"scroll"}), style={"height":"100%"}),
            # dcc.Store( id='session-data' ),
            # dbc.Row( 
            #   dcc.Loading(id="loading-stored-file", children=html.Div(id="output-field", style={"height":"100%","overflow":"scroll"}), style={"height":"100%"}),
            # )
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content



@dashapp.callback(
    Output('input-field', component_property='children'),
    Input('session-id', 'data')
)
def input_field(session_id):
    # header_access, msg_access = check_access( 'agebot' )
    # header_access, msg_access = None, None # for local debugging 
    content=[ 
        dbc.Row( 
            [
              dbc.Col( dcc.Textarea(id='input', placeholder="type here", value="", style={ "width":"100%",'height': 30} ), md=5 ), #, style={ "width":"100%"} )  ), #,'height': 100,
              dbc.Col( html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%",'height': 30}),  md=1), 
            ], 
            style={"margin-top":10},
            justify="center",
        )
    ]
    return content

    # Output('export-session','data'),
                # dcc.Store( id='generate_markers-import'),
# @dashapp.callback(
#     Output('session-data', 'data'),
#     Input("submit-button-state", "n_clicks"),
#     State('input', 'value'),
#     State("output-text","value")
# )
# def session_data(n_clicks, input, current_text):
    
#     print(1, input )
#     print(2, current_text)
    
#     return input + current_text
#     # return None


@dashapp.callback(
    Output('output-field', component_property='children'),
    Output( "session-data", "data"),
    Input( "submit-button-state", "n_clicks"),
    State('input', 'value'),
    State( "session-data", "data")
)
def output_field(n_clicks, input, current ):
    # header_access, msg_access = check_access( 'agebot' )
    # header_access, msg_access = None, None # for local debugging 

    if ( not input ) and ( not current ) :
        return None
    
    import time
    time.sleep(2)

    input="**question: **" + input
    answer="**answer: **" + "some answer"
    output=input + '\n\n' + answer

    if current:
        output=output + "\n\n" + current 

    content=[ 
        dbc.Row( 
            [
              dbc.Col( dcc.Markdown(output, style={"width":"100%", "margin":"2px"}, id="output-text"), md=6 )
            ], 
            style={"margin-top":10},
            justify="center",
        )
    ]
        
    return content, output

@dashapp.callback(
    Output("modal", "is_open"),
    [Input("submit-button-state", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

# navbar toggle for colapsed status
@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

