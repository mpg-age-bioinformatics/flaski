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
    make_navbar, make_footer, make_options, make_table, META_TAGS, GROUPS, GROUPS_INITALS,  make_submission_file
import uuid
import pandas as pd
import os        
from werkzeug import secure_filename


CURRENTAPP="alphafold"
navbar_title="AlphaFold submission form"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})

# generate dropdown options
groups_=make_options(GROUPS)
external_=make_options(["External"])
organisms=["celegans","mmusculus","hsapiens","dmelanogaster","nfurzeri"]
organisms_=make_options(organisms)
ercc_=make_options(["YES","NO"])

example_fasta="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP\
DEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAK\
SVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPHHE\
RCSDSDGLAPPQHLIRVEGNLRVEYLDDRNTFRHSVVVPYEPPEVGSDCTTIHYNYMCNS\
SCMGGMNRRPILTIITLEDSSGNLLGRNSFEVRVCACPGRDRRTEEENLRKKGEPHHELP\
PGSTKRALPNNTSSSPQPKKKPLDGEYFTLQIRGRERFEMFRELNEALELKDAQAGKEPG\
GSRAHSSHLKSKKGQSTSRHKKLMFKTEGPDSD"

def make_submission_json(email,group, name, sequence):
    @cache.memoize(60*60*2) # 2 hours
    def _make_submission_json(email,group, name, sequence):
        filename=make_submission_file(".alphafold.json", folder="mpcdf")
        name=secure_filename(name)
        name=name.replace(" ","_")
        email=email.replace(" ", ",")
        email=email.split(",")
        email=[ e for e in email if e ]
        email=",".join(email)
        sequence=sequence.replace(" ", "")
        sequence=secure_filename(sequence)
        return {"filename":filename,"email": email, "group_name":group, "group_initials":GROUPS_INITALS[group],"name_fasta_header":name, "sequence_fasta":sequence}
    return _make_submission_json(email,group, name, sequence)

# arguments 
arguments=[ 
    dbc.Row( 
        [
            dbc.Col( html.Label('email') ,md=2, style={"textAlign":"right" }), 
            dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value="", type='text', style={ "width":"100%"} ) ,md=5 ),
            dbc.Col( html.Label('your email address'),md=2  ), 
        ], 
        style={"margin-top":10}),
    dbc.Row( 
        [
            dbc.Col( html.Label('Group') ,md=2 , style={"textAlign":"right" }), 
            dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, style={ "width":"100%"}),md=5 ),
            dbc.Col( html.Label('Select from dropdown menu'),md=2  ), 
        ], 
        style={"margin-top":10}),
    dbc.Row( 
        [
            dbc.Col( html.Label('Sequence name') ,md=2 , style={"textAlign":"right" }), 
            dbc.Col( dcc.Input(id='name', placeholder="my sequence name", value="", type='text', style={ "width":"100%"} ) ,md=5 ),
            dbc.Col( html.Label('Fasta header'),md=2  ), 
        ], 
        style={"margin-top":10}),
    dbc.Row( 
        [
            dbc.Col( html.Label('Sequence') ,md=2 , style={"textAlign":"right" }), 
            dbc.Col( dcc.Textarea(id='sequence', placeholder=example_fasta, value="", style={ "width":"100%",'height': 400} ) ,md=5 ),
            dbc.Col( html.Label('Protein sequence'),md=2  ), 
        ], 
        style={"margin-top":10})
]

# input 
controls = [ html.Div(arguments,  id="tab-info") ]
#     dcc.Tabs(
#         dcc.Tab( arguments,label="Info", id="tab-info" ) ,
#     ])
# ]

main_input=[ dbc.Card(controls, body=False),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "200px","margin-top":4, "margin-bottom":4}),
            html.Div(id="message")
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

# main submission call
@dashapp.callback(
    Output('message', component_property='children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('name', 'value'),
    State('sequence', 'value'),
    prevent_initial_call=True )
def update_output(session_id, n_clicks, email,group,name,sequence):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ]
    # if not validate_user_access(current_user,CURRENTAPP):
    #         return dcc.Location(pathname="/index", id="index"), None, None

    if CURRENTAPP not in apps:
        return dbc.Alert('''You do not have access to this App.''',color="danger")

    subdic=make_submission_json( email,group, name, sequence)

    if os.path.isfile(subdic["filename"].replace("json","tsv")):
        msg='''You have already submitted this data. Re-submission will not take place.'''
    else:
        df=pd.DataFrame(subdic, index=[0] ) 
        df=df.transpose()
        df.reset_index(inplace=True, drop=False)
        df.to_csv(subdic["filename"].replace("json","tsv"), sep="\t", index=None, header=False)

        msg='''**Submission successful**. Please check your email for confirmation.'''
    
        if subdic["group_name"] == "External" :
            subdic["filename"]=subdic["filename"].replace("/submissions/", "/tmp/")

        send_submission_email(user=current_user, submission_type="alphafold", submission_file=os.path.basename(subdic["filename"].replace("json","tsv")), attachment_path=subdic["filename"].replace("json","tsv"))

        if subdic["group_name"] == "External" :
            os.remove(subdic["filename"])

    return dcc.Markdown(msg, style={"margin-top":"10px"} )


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