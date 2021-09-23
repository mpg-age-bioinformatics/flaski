from flaski import app
from flask_login import current_user
from flask_caching import Cache
from flaski.email import send_submission_email
from flaski.routines import read_private_apps, separate_apps
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, protect_dashviews, validate_user_access, \
    make_navbar, make_footer, make_options, make_table, META_TAGS, GROUPS, make_submission_file, validate_metadata
import uuid
import pandas as pd
import os

CURRENTAPP="motifenr"
navbar_title="Motif enrichment submission form"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})

# Read in users input and generate submission file.
def generate_submission_file(rows, email,group,project_title,organism,idstype):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(rows, email,group,project_title,organism,idstype):
        rows=rows.replace(" ","\n")
        rows=rows.split("\n")
        rows=[ s for s in rows if s != "" ]
        df=pd.DataFrame({"input":rows})
        df_=pd.DataFrame({"Field":["email","Group","Project title", "Organism", "IDs"],\
                          "Value":[ email,group,project_title, organism,idstype]}, index=list(range(5)))
        df=df.to_json()
        df_=df_.to_json()
        filename=make_submission_file(".motif_enrichment.xlsx")

        return {"filename": filename, "samples":df, "metadata":df_}
    return _generate_submission_file(rows, email,group,project_title,organism,idstype)

# generate dropdown options
groups_=make_options(GROUPS)
external_=make_options(["External"])
organisms=["celegans","mmusculus","hsapiens","dmelanogaster","nfurzeri"]
organisms_=make_options(organisms)
ids_=make_options(["ENSEMBL_GENE_IDS","ENSEMBL_GENE_NAME" ])
motif_tyep=make_options(["DNA","RNA", "PROTEIN"])

list_of_genes=[ "ENSG00000006747","ENSG00000183696","ENSG00000140545","ENSG00000136895","ENSG00000120451",\
    "ENSG00000156976","ENSG00000197937","ENSG00000119125","ENSG00000197355","ENSG00000204103","ENSG00000196924",\
    "ENSG00000119397","ENSG00000100292","ENSG00000224287","ENSG00000148702","ENSG00000205542","ENSG00000184588",\
    "ENSG00000123595","ENSG00000125772","ENSG00000102032","ENSG00000151465","ENSG00000129422","ENSG00000114473",\
    "ENSG00000128335","ENSG00000196547","ENSG00000059804","ENSG00000047644","ENSG00000149591","ENSG00000151838",\
    "ENSG00000179348"]

list_of_genes="\n".join(list_of_genes)

# arguments 
arguments=[ dbc.Row( [
                dbc.Col( html.Label('email') ,md=2 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value="", type='text', style={ "width":"100%"} ) ,md=4 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Group') ,md=2 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, style={ "width":"100%"}),md=4 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Project title') ,md=2 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='project_title', placeholder="my_super_proj", value="", type='text', style={ "width":"100%"} ) ,md=4 ),
                dbc.Col( html.Label('Give a name to your project'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Organism') ,md=2 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-organism', options=organisms_, style={ "width":"100%"}),md=4 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('IDs type') ,md=2 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-ids', options=ids_, style={ "width":"100%"}),md=4 ),
                dbc.Col( html.Label('Input type'),md=3  ), 
                ], style={"margin-top":10,"margin-bottom":10}),
            dbc.Row( [
                dbc.Col( html.Label('Input') ,md=2 , style={ "textAlign":"right" }), 
                dbc.Col( dcc.Textarea( id='input-genes', placeholder=list_of_genes,style={ "width":"100%", 'height': 300 } ),md=4 ),
                dbc.Col( [ html.Label('Links to ensembl releases:'), 
                        dcc.Link( 'relelase-xx', href="https://www.google.com" ) , html.Br(),
                        dcc.Link( 'relelase-xx', href="https://www.google.com" ) , html.Br(),
                        dcc.Link( 'relelase-xx', href="https://www.google.com" ) , html.Br(),
                        dcc.Link( 'relelase-xx', href="https://www.google.com" ) ] , md=3  ), 
                ], style={"margin-top":10,"margin-bottom":10}),          
]

# input 
controls = [
    dcc.Tabs([
        dcc.Tab( arguments,label="Input", id="tab-info" ) ,
    ])
]

main_input=[ dbc.Card(controls, body=False),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "200px","margin-top":4, "margin-bottom":4}),
            html.Div(id="message"),
            html.Div(id="message2")
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
                        children=html.Div(id="main_input"),
                        style={"margin-top":"0%"}
                    ),                    
                    style={"width": "90%", "min-height": "100%","height": "100%",'overflow': 'scroll'} )
            ], 
             style={"min-height": "87vh"}),
    ] ) 
    ] + make_footer()
)

@dashapp.callback(
    Output('message2', component_property='children'),
    Input('session-id', 'data'))
def info_access(session_id):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ]
    # if not validate_user_access(current_user,CURRENTAPP):
    #         return dcc.Location(pathname="/index", id="index"), None, None
    if CURRENTAPP not in apps:
        return dcc.Markdown('''
        
#### !! You have no access to this App !!

        ''', style={"margin-top":"15px"} )

# main submission call
@dashapp.callback(
    Output('message', component_property='children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('input-genes', 'value'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('project_title', 'value'),
    State('opt-organism', 'value'),
    State('opt-ids', 'value'),
    prevent_initial_call=True )
def update_output(session_id, n_clicks, rows, email,group,project_title,organism,idstype):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ]
    # if not validate_user_access(current_user,CURRENTAPP):
    #         return dcc.Location(pathname="/index", id="index"), None, None
    if CURRENTAPP not in apps:
        return dcc.Markdown('''
        
#### !! You have no access to this App !!

        ''', style={"margin-top":"15px"} )
    subdic=generate_submission_file(rows, email, group, project_title, organism, idstype)
    samples=pd.read_json(subdic["samples"])
    metadata=pd.read_json(subdic["metadata"])
    # print(subdic["filename"])

    #{"filename": filename, "samples":df, "metadata":df_}
    validation=validate_metadata(metadata)
    if validation:
        msg='''
#### !! ATTENTION !!

'''+validation
        return dcc.Markdown(msg, style={"margin-top":"15px"} )

    if os.path.isfile(subdic["filename"]):
        msg='''You have already submitted this data. Re-submission will not take place.'''
    else:
        msg='''**Submission successful**. Please check your email for confirmation.'''
    
    if metadata[  metadata["Field"] == "Group"][ "Value" ].values[0] == "External" :
        subdic["filename"]=subdic["filename"].replace("/submissions/", "/tmp/")

    EXCout=pd.ExcelWriter(subdic["filename"])
    samples.to_excel(EXCout,"samples",index=None)
    metadata.to_excel(EXCout,"motif_enrichment",index=None)
    EXCout.save()

    send_submission_email(user=current_user, submission_type="motif_enrichment", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])

    if metadata[  metadata["Field"] == "Group"][ "Value" ].values[0] == "External" :
        os.remove(subdic["filename"])

    return dcc.Markdown(msg, style={"margin-top":"10px"} )

# add rows buttom 
@dashapp.callback(
    Output('adding-rows-table', 'data'),
    Input('editing-rows-button', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('adding-rows-table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

# this call back prevents the side bar from being shortly 
# shown / exposed to users without access to this App
@dashapp.callback( Output('app_access', 'children'),
                   Output('main_input', 'children'),
                   Output('navbar','children'),
                   Input('session-id', 'data') )
def get_side_bar(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return dcc.Location(pathname="/index", id="index"), None, None, None
    else:
        navbar=make_navbar(navbar_title, current_user, cache)
        return None, main_input, navbar


# options and values based on in-house vs external users
@dashapp.callback( Output("opt-group","options"),
                   Output("opt-group","value"),
                   Input('session-id', 'data') )
def make_readme(session_id):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ] 
        
    if "@age.mpg.de" in current_user.email:
        return groups_, None
    else:
        return external_, "External"

# update user email on email field on start
@dashapp.callback( Output('email','value'),
                   Input('session-id', 'data') )
def set_email(session_id):
    return current_user.email

# navbar toggle for colapsed status
@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open