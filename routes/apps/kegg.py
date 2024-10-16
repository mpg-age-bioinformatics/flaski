from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from flask_login import current_user
from flask_caching import Cache
from flask import session, send_from_directory, abort, send_file
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import make_options, encode_session_app
from myapp.routes.apps._utils import parse_import_json, make_except_toast, ask_for_help, save_session, make_min_width
import os
import uuid
from werkzeug.utils import secure_filename
from time import sleep
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from pyflaski.violinplot import make_figure

#from flaski.routines import check_session_app
from dash.exceptions import PreventUpdate
from pyflaski.kegg import make_figure, figure_defaults
import traceback
import json
import pandas as pd
import time
import plotly.express as px
# from plotly.io import write_image
import plotly.graph_objects as go
from ._kegg import compound_options, pathway_options, organism_options, network_pdf
from dash import dash_table

import io
from Bio.KEGG.KGML.KGML_parser import read
from Bio.Graphics.KGML_vis import KGMLCanvas


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("kegg",url_base_pathname=f'{PAGE_PREFIX}/kegg/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="KEGG", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    
# Route to serve any file from /tmp directory
@dashapp.server.route(f"{PAGE_PREFIX}/kegg/tmp/<path:filename>")
def serve_file_from_tmp(filename):
    tmp_dir = "/tmp"

    if not filename.startswith("kegg-") or not filename.endswith(".pdf"):
        return abort(403, description="Forbidden: Only PDF files with kegg initials are allowed")
    
    file_path = os.path.abspath(os.path.join(tmp_dir, filename))

    # Check if the file exists and is within the /tmp directory
    if os.path.exists(file_path):
        return send_file(file_path, mimetype='application/pdf')
    else:
        return abort(404, description="File not found")
    

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
    eventlog = UserLogging(email=current_user.email, action="visit kegg")
    db.session.add(eventlog)
    db.session.commit()

    # For better loading
    def make_loading(children,i):
        return dcc.Loading(
            id=f"menu-load-{i}",
            type="default",
            children=children,
        )

    # HTML content from here
    protected_content=html.Div(
        [
            make_navbar_logged("KEGG",current_user),
            html.Div(id="app_access"),
            # html.Div(id="redirect-app"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),

            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [
                                    html.H5("Filters", style={"margin-top":10}), 
                                    html.Label('Compound'), make_loading( dcc.Dropdown( id='opt-compound', multi=True, style={'white-space': 'nowrap','text-overflow': 'ellipsis'}), 1),
                                    html.Label('Pathway',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-pathway'), 2 ),
                                    html.Label('Organism',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-organism', placeholder="No Pathway Selected"), 3 ),
                                    html.Label('Download file prefix',style={"margin-top":10}), 
                                    dcc.Input(id='download_name', value="kegg", type='text',style={"width":"100%", "height":"34px"})
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
                        xs=12,sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","margin-bottom":"50px"} 
                    ),               
                    dbc.Col(
                        [
                          dcc.Loading(
                              id="loading-output-1",
                              type="default",
                              children=[ html.Div(id="my-output")],
                              style={"margin-top":"50%"} 
                          ),  
                          dcc.Markdown("Based on KEGG (Kyoto Encyclopedia of Genes and Genomes) - https://www.genome.jp/kegg/", style={"margin-top":"15px", "margin-left":"15px"}),
                        ],
                        xs=12,sm=12,md=6,lg=8,xl=9,
                        style={"margin-bottom":"50px"}
                    )
                ],
                align="start",
                justify="left",
                className="g-0",
                style={"width":"100%"}
            ),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

# Callback to load compound list on session load
@dashapp.callback(
    Output(component_id='opt-compound', component_property='options'),
    Input('session-id', 'data')
    )
def update_menus(session_id):
    return compound_options(cache)

# Callback to update opt-pathway based on selected compounds
@dashapp.callback(
    Output('opt-pathway', 'options'),
    Output('opt-pathway', 'placeholder'),
    Input('opt-compound', 'value')
)
def update_pathways(selected_compounds):
    if selected_compounds is None or len(selected_compounds) == 0:
        return [], "No Compound Selected"    
    pw_options=pathway_options(cache, selected_compounds)
    if pw_options is None:
        return [], "No Pathway Found for Selected Compound" 
    return pw_options, "Select Pathway"

# Callback to update opt-organism based on selected pathway
@dashapp.callback(
    Output('opt-organism', 'options'),
    Output('opt-organism', 'placeholder'),
    Input('opt-pathway', 'value')
)
def update_organisms(selected_pathway):
    if selected_pathway is None:
        return [], "No Pathway Selected"    
    org_options=organism_options(cache, selected_pathway)
    if org_options is None:
        return [], "No Organism Found for Selected Pathway" 
    return org_options, "Select Organism"


# Callback on submit
@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-compound", "value"),
    State("opt-pathway", "value"),
    State("opt-organism", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, compound, pathway, organism, download_name):
    if not n_clicks:
        return html.Div([])
    
    if not compound or pathway is None or organism is None:
        return html.Div([dcc.Markdown("*** Please select at least a compound, pathway and organism!", style={"margin-top":"15px","margin-left":"15px"})])
    
    pdf_path=network_pdf(compound,pathway,organism)
    if pdf_path is None:
        return html.Div([dcc.Markdown("*** Failed to generate network pdf!", style={"margin-top":"15px","margin-left":"15px"})])

    output= html.Div([
        html.Iframe(src=f"{PAGE_PREFIX}/kegg{pdf_path}", style={"width": "100%", "height": "700px"}),
    ])

    return output

