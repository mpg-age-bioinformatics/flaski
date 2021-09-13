from flaski import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, parse_table, protect_dashviews, validate_user_access, make_navbar, make_footer, make_options
from ._aadatalake import read_results_files, read_gene_expression, read_genes, read_significant_genes, \
    filter_samples, filter_genes, filter_gene_expression
import uuid
import dash_table

# import pandas as pd
import os

CURRENTAPP="aadatalake"
navbar_title="RNAseq data lake"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , server=app, external_stylesheets=[dbc.themes.BOOTSTRAP])
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
    html.Label('Download name',style={"margin-top":10}), dcc.Input(id='download_name', value="data.lake", type='text') ]

side_bar=[ dbc.Card(controls, body=True),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%","margin-top":4} )
         ]

# Define Layout
dashapp.layout = html.Div( [ html.Div(id="navbar"), dbc.Container(
    fluid=True,
    children=[
        html.Div(id="app_access"),
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dbc.Row(
            [
                dbc.Col( id="side_bar", md=3, style={"height": "100%",'overflow': 'scroll'} ),
                dbc.Col( id='my-output', md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"height": "87vh"}),
    ] ) 
    ] + make_footer()
)

## all callback elements with `State` will be updated only once submit is pressed
## all callback elements wiht `Input` will be updated everytime the value gets changed 
@dashapp.callback(
    Output(component_id='my-output', component_property='children'),
    Output(component_id='opt-groups', component_property='options'),
    Output(component_id='opt-samples', component_property='options'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    Input("opt-datasets", "value"),
    Input("opt-groups", "value"),
    Input("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State(component_id='download_name', component_property='value'),
)
def update_output(session_id, n_clicks, datasets, groups, samples, genenames, geneids, download_name):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)    
    groups_=list(set(selected_results_files["Group"]))
    groups_=make_options(groups_)

    selected_results_files, ids2labels=filter_samples(datasets=datasets, groups=groups,cache=cache)    
    reps_=list(set(selected_results_files["Reps"]))
    reps_=make_options(reps_)

    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    
    results_files_=selected_results_files[["Set","Group","Reps"]]
    results_files_.columns=["Set","Group","Sample"]
    results_files_=results_files_.drop_duplicates()      

    results_files_=dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in results_files_.columns],
        data=results_files_.to_dict('records'),
        fixed_rows={ 'headers': True, 'data': 0 },
        style_cell={
            'whiteSpace': 'normal'
        },
        virtualization=True,
        style_table={'height': 800, 'overflowY': 'auto'},
        page_size=50
        # page_action='none'
        )
    
    # if not active_tab:
        # active_tab="tab-samples"
    out=dbc.Tabs(
        [
           dbc.Tab(results_files_, label="Samples", tab_id="tab-samples"), 
           dbc.Tab(label="Gene expression", tab_id="tab-geneexpression"), 
        ],
        id="card-tabs",
        active_tab="tab-samples"
        # card=True
    )
    return out, groups_, reps_

@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Input('session-id', 'data'),
    )
def update_datasets(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    results_files=read_results_files(cache)
    datasets=list(set(results_files["Set"]))
    datasets=make_options(datasets)
    return datasets

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