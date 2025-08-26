from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_options, GROUPS, make_submission_file, send_submission_email, GROUPS_INITALS
import os
import uuid
import io
import base64
import re
import pandas as pd
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename



FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("alphafold",url_base_pathname=f'{PAGE_PREFIX}/alphafold/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="AlphaFold 3" , assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit alphafold")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("AlphaFold 3",current_user),
            html.Div(id="app-content",style={"height":"100%","overflow":"scroll"}),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

def make_submission_json(email,group, name, sequence):
    @cache.memoize(7200) # 2 hours
    def _make_submission_json(email,group, name, sequence):
        def clean_seqs(sequence):
            sequence=sequence.replace(" ", "")
            sequence=secure_filename(sequence)
            sequence=sequence.upper()
            return sequence

        def clean_header(name):
            name = re.sub(r'[^A-Z-]', '', name.upper())
            name = re.sub(r'(?<!-)-(?!-)', '', name)
            name = re.sub(r'-{2,}', '--', name)
            if '--' in name:
                before, after = name.split('--', 1)
                after = after.replace('--', '')
                before = before[:25]
                name = before + '--' + after
            else:
                name = name[:25]

            name = secure_filename(name)
            return name

        filename=make_submission_file(".alphafold.json", folder="mpcdf")
        name=clean_header(name)
        email=email.replace(" ", ",")
        email=email.split(",")
        email=[ e for e in email if e ]
        email=",".join(email)

        if ">" in sequence :
            sequence=sequence.split(">")
            sequence=[ s.split("\n") for s in sequence ]
            sequence=[ [ ">"+clean_header(s[0]), clean_seqs(s[1]) ]  for s in sequence if len(s) > 1 ]
            sequence=[ ";".join( s ) for s in sequence ]
            sequence=";".join(sequence)
        else:
            sequence=clean_seqs(sequence)
        return {"filename":filename,"email": email, "group_name":group, "group_initials":GROUPS_INITALS[group],"name_fasta_header":name, "sequence_fasta":sequence}
    return _make_submission_json(email,group, name, sequence)



@dashapp.callback(
    Output('app-content', component_property='children'),
    Input('session-id', 'data'))
def make_app_content(session_id):
    # header_access, msg_access = check_access( 'alphafold' )
    # header_access, msg_access = None, None # for local debugging 

    # generate dropdown options
    groups_=make_options(GROUPS)
    external_=make_options(["External"])

    example_fasta="MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGP\
DEAPRMPEAAPPVAPAPAAPTPAAPAPAPSWPLSSSVPSQKTYQGSYGFRLGFLHSGTAK\
SVTCTYSPALNKMFCQLAKTCPVQLWVDSTPPPGTRVRAMAIYKQSQHMTEVVRRCPH\n\n\
..or multifasta, for multimers:\n\n\
>PROTEINA\n\
MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDIEQWFTEDPGPDEAPRM\n\
>PROTEINB\n\
GPDSMEEVVVPEEPPKLVSALATYVQQERLCTMFLSIANKLLPLKPHACHLKRIRRSSATRVATAPMD\n\
>DNAA--DNA\n\
CCGCGCCTGTGGGATCTGCATGCCCC\n\
>RNAA--RNA\n\
GGCCGCUUAGCACAGUGGCAGUGCACCACUCUCGUAAAGUGGGGGUCGCGAGUUCGAUUCUCGCAGUGGCCUCCA"

    content=[ 
        dbc.Card(
            [ 
                dbc.Row( 
                    [
                        dbc.Col( html.Label('Email') ,md=2, style={"textAlign":"right" }), 
                        dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%"} ) ,md=5 ),
                        dbc.Col( html.Label('Your email address'),md=4  ), 
                    ], 
                    style={"margin-top":10}),
                dbc.Row( 
                    [
                        dbc.Col( html.Label('Group') ,md=2 , style={"textAlign":"right" }), 
                        dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, style={ "width":"100%"}),md=5 ),
                        dbc.Col( html.Label('Select from dropdown menu'),md=4  ), 
                    ], 
                    style={"margin-top":10}),
                dbc.Row( 
                    [
                        dbc.Col( html.Label('Sequence Name') ,md=2 , style={"textAlign":"right" }), 
                        dbc.Col( dcc.Input(id='name', placeholder="my sequence name", value="", type='text', style={ "width":"100%"} ) ,md=5 ),
                        dbc.Col( html.Label('Fasta header'),md=4  ), 
                    ], 
                    style={"margin-top":10}),
                dbc.Row( 
                    [
                        dbc.Col( html.Label('Sequence') ,md=2 , style={"textAlign":"right" }), 
                        dbc.Col( dcc.Textarea(id='sequence', placeholder=example_fasta, value="", style={ "width":"100%",'height': 400} ) ,md=5 ),
                        dbc.Col(
                            html.Div([
                                html.Label('Protein/DNA/RNA sequence(s)'),
                                html.Br(),
                                html.Br(),
                                html.Label("Guidelines:"),
                                html.Ul([
                                    html.Li([
                                        "For multi-FASTA, use ",
                                        html.Code(">SEQUENCENAME"),
                                        " on one line, then ",
                                        html.Code("SEQUENCE"),
                                        " on the next"
                                    ]),
                                    html.Li("SEQUENCENAME should contain only A–Z and be at most 25 characters"),
                                    html.Li([
                                        "For DNA or RNA sequences, write ",
                                        html.Code(">SEQUENCENAME--DNA"),
                                        " or ",
                                        html.Code(">SEQUENCENAME--RNA")
                                    ]),
                                    html.Li("By default, the sequence is treated as Protein"),
                                ], className="mb-0"),
                                html.Br(),
                            ]),
                            md=4,
                        ), 
                    ], 
                    style={"margin-top":10}),
                
                dbc.Row(
                    [
                        dbc.Col(md=2),
                        dbc.Col(
                            dbc.Checkbox(
                                id="agree",
                                value=False,
                                label=html.Span([
                                    "I have read and agree to the ",
                                    html.A(
                                        "AlphaFold 3 Output Terms of Use",
                                        href="https://github.com/google-deepmind/alphafold3/blob/main/OUTPUT_TERMS_OF_USE.md",
                                        target="_blank",
                                        rel="noopener noreferrer",
                                    ),
                                ]),
                            ),
                            md=5,
                        )
                    ],
                    style={"margin-top": 10},
                ),

            ], 
            body=False
        ),
        html.Button(id='submit-button-state', n_clicks=0, children='Submit', disabled=True, style={"width": "200px","margin-top":4, "margin-bottom":"50px"}),
        dbc.Modal(
            dcc.Loading(
                id=f"modal-load",
                type="default",
                children=
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Whoopss..",id="modal_header") ),
                        dbc.ModalBody("something went wrong!", id="modal_body"),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
            ),
            id="modal",
            is_open=False,
        ),
        dcc.Download( id="download-file" )
    ]

    return content

# main submission call
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    Output("download-file","data"),
    Input('submit-button-state', 'n_clicks'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('name', 'value'),
    State('sequence', 'value'),
    prevent_initial_call=True )
def update_output(n_clicks, email,group,name,sequence):
    header, msg = check_access( 'alphafold' )
    # header, msg = None, None    
    if msg :
        return header, msg, dash.no_update

    subdic=make_submission_json( email,group, name, sequence)

    if os.path.isfile(subdic["filename"].replace("json","tsv")):
        header="Attention"
        msg='''You have already submitted this data. Re-submission will not take place.'''
    else:
        df=pd.DataFrame(subdic, index=[0] ) 
        df=df.transpose()
        df.reset_index(inplace=True, drop=False)
        df.to_csv(subdic["filename"].replace("json","tsv"), sep="\t", index=None, header=False)
        header="Success!"
        msg='''Please allow a summary file of your submission to download and check your email for confirmation.'''
        send_submission_email(user=current_user, submission_type="AlphaFold", submission_tag=subdic["filename"].replace("json","tsv"), submission_file=None, attachment_path=None)

    return header, msg, dcc.send_file(subdic["filename"].replace("json","tsv"))

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

# Submit button enabled when values are filled
@dashapp.callback(
    Output('submit-button-state', 'disabled'),
    Input('email', 'value'),
    Input('opt-group', 'value'),
    Input('name', 'value'),
    Input('sequence', 'value'),
    Input('agree', 'value'),
)
def toggle_submit_disabled(email, group, name, sequence, agreed):
    def _filled(x):
        return bool(x and str(x).strip())
    all_filled = _filled(email) and _filled(group) and _filled(name) and _filled(sequence)
    return not (all_filled and bool(agreed))
