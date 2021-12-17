from myapp import app
from flask_login import current_user
from flask_caching import Cache
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
import pandas as pd
import time
import plotly.express as px
# from plotly.io import write_image
import plotly.graph_objects as go
from werkzeug.utils import secure_filename


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("storage",url_base_pathname='/storage/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
})

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
# card_body_style={ "padding":"2px", "padding-top":"4px","padding-left":"18px"}


@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    protected_content=html.Div(
        [
            make_navbar_logged("Storage",current_user),
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
    finder=dbc.Card(
        dbc.Form(
            [ 
                html.H2("tmp-files-table", style={'textAlign': 'center'} ),
            ]
        ),
        body=True
    )



    page=dbc.Row( 
        [
            dbc.Col( 
                [ 
                    finder
                ],
                sm=12,md=12, lg=10, xl=8, 
                align="center", 
                style={ "margin-left":2, "margin-right":2 ,'margin-bottom':"50px"}
            ),
        ],
        align="center",
        justify="center",
        style={"min-height": "95vh", 'verticalAlign': 'center'}
    )
    return page
    