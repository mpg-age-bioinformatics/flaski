import re
from flaski import app
from flask_login import current_user
from flask_caching import Cache
from flaski.routines import check_session_app
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, parse_table, protect_dashviews, validate_user_access, \
    make_navbar, make_footer, make_options, make_table, META_TAGS, make_min_width, \
    change_table_minWidth, change_fig_minWidth
import uuid
from werkzeug.utils import secure_filename
import json
from flask import session

import pandas as pd
import os

CURRENTAPP="rnaseq"
navbar_title="RNAseq submission form"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})

controls = [ 
    html.H5("Filters", style={"margin-top":10}), 
    html.Label('Data sets'), dcc.Dropdown( id='opt-datasets', multi=True),
    html.Label('Groups',style={"margin-top":10}), dcc.Dropdown( id='opt-groups', multi=True),
    html.Label('Samples',style={"margin-top":10}), dcc.Dropdown( id='opt-samples', multi=True),
    html.Label('Gene names',style={"margin-top":10}), dcc.Dropdown( id='opt-genenames', multi=True),
    html.Label('Gene IDs',style={"margin-top":10}), dcc.Dropdown( id='opt-geneids', multi=True),
    html.Label('Download file prefix',style={"margin-top":10}), dcc.Input(id='download_name', value="data.lake", type='text') ]

# controls = [ 

# ]

side_bar=[ dbc.Card(controls, body=True),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%","margin-top":4, "margin-bottom":4} )
         ]

# Define Layout
dashapp.layout = html.Div( [ html.Div(id="navbar"), dbc.Container(
    fluid=True,
    children=[
        html.Div(id="app_access"),
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dbc.Row(
            [
                dbc.Col( dcc.Loading( 
                        id="loading-output-1",
                        type="default",
                        children=html.Div(id="side_bar"),
                        style={"margin-top":"0%"}
                    ),                    
                    style={"width": "90%", "height": "100%",'overflow': 'scroll'} ),               
                # dbc.Col( dcc.Loading(
                #         id="loading-output-2",
                #         type="default",
                #         children=[ html.Div(id="my-output")],
                #         style={"margin-top":"50%","height": "100%"} ),
                #     md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"min-height": "87vh"}),
    ] ) 
    ] + make_footer()
)

@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Output(component_id='opt-genenames', component_property='options'),
    Output(component_id='opt-geneids', component_property='options'),
    Input('session-id', 'data')
    )
def update_datasets(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    results_files=read_results_files(cache)
    datasets=list(set(results_files["Set"]))
    datasets=make_options(datasets)

    genes=read_genes(cache)

    genenames=list(set(genes["gene_name"]))
    genenames=make_options(genenames)

    geneids=list(set(genes["gene_id"]))
    geneids=make_options(geneids)

    return datasets, genenames, geneids

# this call back prevents the side bar from being shortly 
# show / exposed to users without access to this App
@dashapp.callback( Output('app_access', 'children'),
                   Output('side_bar', 'children'),
                   Output('navbar','children'),
                   Input('session-id', 'data') )
def get_side_bar(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return dcc.Location(pathname="/index", id="index"), None, None
    else:
        navbar=make_navbar(navbar_title, current_user, cache)
        return None, side_bar, navbar

@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', debug=True, port=8050)

# #### HANDLING LARGE AMOUNT OF ARGUMENTS ####
# #### this will work for inputs with only one present in the list of Inputs+States
# ## all callback elements with `State` will be updated only once submit is pressed
# ## all callback elements wiht `Input` will be updated everytime the value gets changed 
# inputs=[Input('submit-button-state', 'n_clicks')]
# states=[State('upload-data', 'contents'),
#     State("opt-xcol", "search_value"),
#     State(component_id='multiplier', component_property='value'),
#     State('upload-data', 'filename'),
#     State('upload-data', 'last_modified') ]
# @app.callback(
#     Output(component_id='my-output', component_property='children'),
#     inputs,
#     states
#     )      
# def update_output(*args):
#     input_names = [item.component_id for item in inputs + states]
#     kwargs_dict = dict(zip(input_names, args))
#     print(kwargs_dict)
#     multiplier=kwargs_dict["multiplier"]