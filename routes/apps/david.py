from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
#from flaski.routines import check_session_app
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, make_table, encode_session_app
from pyflaski.david import run_david, figure_defaults
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

dashapp = dash.Dash("david",url_base_pathname=f'{PAGE_PREFIX}/david/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
})



def run_david_and_cache(pa,cache):
    @cache.memoize(timeout=3600)
    def _run_david_and_cache(pa,cache):
        print("Running  fresh")
        import sys ; sys.stdout.flush()
        df, report_stats, empty =run_david(pa)

        df=df.astype(str)
        report_stats=report_stats.astype(str)
        david_results={ "df": df.to_json() , "stats": report_stats.to_json() }
        return david_results
    return _run_david_and_cache(pa,cache)


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
    protected_content=html.Div(
        [
            make_navbar_logged("DAVID",current_user),
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
    pa=figure_defaults()
    side_bar=[
        dbc.Card( 
            [   
                html.Div(
                    dcc.Upload(
                        id='upload-data',
                        children=html.Div(
                            [ 'Drag and Drop or ',html.A('Select File',id='upload-data-text') ],
                            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
                        ),
                        style={
                            'width': '100%',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            "margin-bottom": "10px",
                            "display":"none"
                        },
                        multiple=False,
                    ),
                ),
                ############################
                dbc.Row(
                        dbc.Label("Target Genes"), #"height":"35px",
                ),
                ############################
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Textarea(id='ids', placeholder=pa["ids"], style={"height":"100px","width":"100%"}),
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                ############################
                dbc.Row(
                        dbc.Label("Background Genes"), #"height":"35px",
                ),
                ############################
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Textarea( id='ids_bg', placeholder=pa["ids_bg"], style={"height":"100px","width":"100%"}),
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                ############################
                # dbc.Row([
                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                # ],
                # className="g-0",
                # ),
                # ############################
                # dbc.Row(
                #         dbc.Label("Arguments"), #"height":"35px",
                # ),
                ############################
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Categories", color="black", id={'type':"dynamic-card","index":"categories"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Gene Ontology", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_gene_ontology"]), value=pa["categories_gene_ontology_value"],  id='categories_gene_ontology_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Gene Domains", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_gene_domains"]), value=pa["categories_gene_domains_value"],  id='categories_gene_domains_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Pathways", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_pathways"]), value=pa["categories_pathways_value"],  id='categories_pathways_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("General Annotations", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_general_annotations"]), value=pa["categories_general_annotations_value"],  id='categories_general_annotations_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Functional Categories", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_functional_categories"]), value=pa["categories_functional_categories_value"],  id='categories_functional_categories_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Protein-Protein interactions", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_protein_protein_interactions"]), value=pa["categories_protein_protein_interactions_value"],  id='categories_protein_protein_interactions_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Literature", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_literature"]), value=pa["categories_literature_value"],  id='categories_literature_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                # ],
                                # className="g-1",
                                # ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Disease", width=4),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["categories_disease"]), value=pa["categories_disease_value"],  id='categories_disease_value', multi=True),
                                            width=8
                                        )
                                    ],
                                    # row=True,
                                    className="g-1",
                                    style= {"margin-top":"2px"}
                                ),
                                ############################
                                    ## example card body row
                                    # dbc.Row(
                                    #     [

                                    #         dbc.Label("Width", width="auto",style={"margin-right":"2px"}),
                                    #         dbc.Col(
                                    #             dcc.Input(id='fig_width', placeholder="eg. 600", type='text', style=card_input_style),
                                    #             style={"margin-right":"5px"}
                                    #         ),
                                    #         dbc.Label("Height", width="auto",style={"margin-right":"2px", "margin-left":"5px"}),
                                    #         dbc.Col(
                                    #             dcc.Input(id='fig_height', placeholder="eg. 600", type='text',style=card_input_style  ) ,
                                    #         ),
        
                                    #     ],
                                    #     className="g-0",
                                    # ),
                                    ## end of example card body row
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"categories"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Input", color="black", id={'type':"dynamic-card","index":"input"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Database",html_for="database_value", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=4
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(options=make_options(pa["database"]), value=pa["database_value"], placeholder="database_value", id='database_value', multi=False, clearable=False, style=card_input_style),
                                        width=8
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("DAVID registered email",html_for="user", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=6
                                    ),
                                    dbc.Col(
                                        dcc.Input(placeholder=pa["user"], id='user',style=card_input_style),
                                        width=6
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Target list name",html_for="name", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=6
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["name"], id='name',style=card_input_style),
                                        width=6
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Background list name",html_for="name_bg", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=6
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["name_bg"], id='name_bg',style=card_input_style),
                                        width=6
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"input"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Cut-offs", color="black", id={'type':"dynamic-card","index":"cutoffs"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Number of genes per term",html_for="n", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=6
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["n"], id='n',style=card_input_style),
                                        width=6
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("p-value",html_for="p", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=6
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["p"], id='p',style=card_input_style),
                                        width=6
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"cutoffs"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
            ],
            body=True,
            style={"min-width":"372px","width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"0px"}#,'display': 'block'}#,"max-width":"375px","min-width":"375px"}"display":"inline-block"
        ),
        dbc.Row(
            [
                dbc.Col( 
                    [
                        dbc.Button(
                            html.Span(
                                [ 
                                    html.I(className="fas fa-file-export"),
                                    " Export" 
                                ]
                            ),
                            color="secondary",
                            id='export-session-btn', 
                            style={"width":"100%"}
                        ),
                        dcc.Download(id="export-session")
                    ],
                    id="export-session-div",
                    width=4,
                    style={"padding-right":"2px"}

                ),
                dbc.Col(
                    [
                        dbc.Button(
                            html.Span(
                                [ 
                                    html.I(className="far fa-lg fa-save"), #, style={"size":"12px"}
                                    " Save" 
                                ]
                            ),
                            id='save-session-btn', 
                            color="secondary",
                            style={"width":"100%"}
                        ),
                        dcc.Download(id="save-session")
                    ],
                    id="save-session-div",
                    width=4,
                    style={"padding-left":"2px", "padding-right":"2px"}
                ),

                dbc.Col( 
                    [
                        dbc.Button(
                            html.Span(
                                [ 
                                    html.I(className="fas fa-lg fa-save"),
                                    " Save as.." 
                                ]
                            ),
                            id='saveas-session-btn', 
                            color="secondary",
                            style={"width":"100%"}
                        ),
                        dcc.Download(id="saveas-session")
                    ],
                    id="saveas-session-div",
                    width=4,
                    style={"padding-left":"2px"}

                ),
            ],
            style={ "min-width":"372px","width":"100%", "display": "none"},
            className="g-0",    
            # style={ "margin-left":"0px" , "margin-right":"0px"}
        ),
        dbc.Button(
                    'Submit',
                    id='submit-button-state', 
                    color="secondary",
                    n_clicks=0, 
                    style={"min-width":"372px","width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
                )
    ]

    app_content=html.Div(
        [
            dcc.Store( id='session-data' ),
            # dcc.Store( id='json-import' ),
            dcc.Store( id='update_labels_field-import'),
            dcc.Store( id='generate_markers-import'),
            dbc.Row( 
                [
                    dbc.Col(
                        side_bar,
                        sm=12,md=6,lg=5,xl=4,
                        align="top",
                        style={"padding":"0px","overflow":"scroll"},
                    ),
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-fig-output",
                                type="default",
                                children=[
                                    html.Div(id="fig-output"),
                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results" 
                                                    ]
                                                ),
                                                id='save-excel-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='save-excel')
                                        ],
                                        id="save-excel-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),                                    
                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-chart-bar"),
                                                        " Cellplot" 
                                                    ]
                                                ),
                                                id='cellplot-session-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='cellplot-session')
                                        ],
                                        id="cellplot-session-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),                                    
                                ],
                                style={"height":"100%"}
                            ),
                            html.Div(
                                [
                                    html.Div( id="toast-read_input_file"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"read_input_file" }), 
                                    html.Div( id="toast-make_fig_output" ),
                                    dcc.Store( id={ "type":"traceback", "index":"make_fig_output" }), 
                                    html.Div(id="toast-email"),  
                                ],
                                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
                            ),
                        ],
                        id="col-fig-output",
                        sm=12,md=6,lg=7,xl=8,
                        align="top",
                        style={"height":"100%"}
                    ),

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), # dbc.ModalTitle(
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='excel-filename', value="david.xlsx", type='text', style={"width":"100%"})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Download", id="excel-filename-download", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="excel-filename-modal",
                        is_open=False,
                    ),

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), 
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='export-filename', value="david.json", type='text', style={"width":"100%"})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Download", id="export-filename-download", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="export-filename-modal",
                        is_open=False,
                    )
                ],
            align="start",
            justify="left",
            className="g-0",
            style={"height":"86vh","width":"100%","overflow":"scroll"}
            ),
        ]
    )
    return app_content

# example reading session from server storage
@dashapp.callback( 
    Output('upload-data', 'contents'),
    Output('upload-data', 'filename'),
    Output('upload-data', 'last_modified'),
    Input('session-id', 'data'))
def read_session_redis(session_id):
    if "session_data" in list( session.keys() )  :
        print(session["session_data"])
        imp=session["session_data"]
        del(session["session_data"])
        from time import sleep
        sleep(2)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update
   

states=[
    State('ids', 'value'),
    State('ids_bg', 'value'),
    State('categories_gene_ontology_value', 'value'),
    State('categories_gene_domains_value', 'value'),
    State('categories_pathways_value', 'value'),
    State('categories_general_annotations_value', 'value'),
    State('categories_functional_categories_value', 'value'),
    State('categories_protein_protein_interactions_value', 'value'),
    State('categories_literature_value', 'value'),
    State('categories_disease_value', 'value'),
    State('database_value', 'value'),
    State('user', 'value'),
    State('name', 'value'),
    State('name_bg', 'value'),
    State('n', 'value'),
    State('p', 'value'),
]    

@dashapp.callback( 
    Output('fig-output', 'children'),
    Output('toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    Output('save-excel-div', 'style'),
    Output('cellplot-session-div', 'style'),
    Output('export-session','data'),
    Output('save-excel', 'data'),
    Input("submit-button-state", "n_clicks"),
    Input("export-filename-download","n_clicks"),
    Input("save-session-btn","n_clicks"),
    Input("saveas-session-btn","n_clicks"),
    Input("excel-filename-download","n_clicks"),
    Input("cellplot-session-btn","n_clicks"),
    [ State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('export-filename','value'),
    State('excel-filename', 'value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,save_excel_btn, cellplot_session_btn,session_id,contents,filename,last_modified,export_filename,excel_filename,upload_data_text, *args):
    ## This function can be used for the export, save, and save as by making use of 
    ## Determining which Input has fired with dash.callback_context
    ## in https://dash.plotly.com/advanced-callbacks
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    download_buttons_style_show={"max-width":"150px","width":"100%","margin":"4px",'display': 'inline-block'} 
    download_buttons_style_hide={"max-width":"150px","width":"100%","margin":"4px",'display': 'none'} 
    try:
        input_names = [item.component_id for item in states]

        if filename and filename.split(".")[-1] == "json":
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "david")
            print(app_data.keys())
            pa = app_data["pa"]
        else:
            pa=figure_defaults()
            for k, a in zip(input_names,args) :
                if type(k) != dict :
                    pa[k]=a

        session_data={ "session_data": {"app": { "david": {'last_modified':last_modified,"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"david")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, download_buttons_style_hide, None, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="david.json"
        export_filename=secure_filename(export_filename)
        if export_filename.split(".")[-1] != "json":
            export_filename=f'{export_filename}.json'  

        def write_json(export_filename,session_data=session_data):
            export_filename.write(json.dumps(session_data).encode())
            # export_filename.seek(0)

        return dash.no_update, None, None, None, dash.no_update, dash.no_update,dcc.send_bytes(write_json, export_filename), None

    if button_id == "save-session-btn" :
        try:
            if filename and filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None, dash.no_update,dash.no_update, None, None, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update,dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"david")
            return dash.no_update, toast, None, tb_str, dash.no_update,  dash.no_update, None, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update,  dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    if button_id == "excel-filename-download":
        if not excel_filename:
            excel_filename=secure_filename("david_results.%s.xlsx" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        excel_filename=secure_filename(excel_filename)
        if excel_filename.split(".")[-1] != "xlsx":
            excel_filename=f'{excel_filename}.xlsx'  

        david_results=run_david_and_cache(pa, cache)
        df = pd.read_json(david_results["df"]) 
        report_stats = pd.read_json(david_results["stats"])

        #excel_file_name = secure_filename("david_results.%s.xlsx" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        import io
        output = io.BytesIO()
        writer= pd.ExcelWriter(output)
        df.to_excel(writer, sheet_name = 'david results', index = False)
        report_stats.to_excel(writer, sheet_name = 'report stats', index = False)
        writer.save()
        data=output.getvalue()
        return dash.no_update, None, None, None, dash.no_update, dash.no_update,None, dcc.send_bytes(data, excel_filename)


    if button_id == "cellplot-session-btn":
        david_results=run_david_and_cache(pa, cache)
        df = pd.read_json(david_results["df"])
        print(df.head())
        #reset_info=check_session_app(session,"iscatterplot",current_user.user_apps)

        cp_pa=dict()
        cp_pa["terms_column"] = "Term"
        cp_pa["david_gene_ids"] = "Genes"
        cp_pa["plotvalue"] = "PValue"
        cp_pa["categories_column"] = "Category"
        cp_pa["annotation_column_value"] = "annotation_2"
        cp_pa["annotation2_column_value"] = "annotation_1"
        cp_pa["gene_identifier"]=None
        cp_pa["expression_values"]=None
        cp_pa["gene_name"]=None

        session_data={ "session_data": {"app": { "cellplot": {"filename":"<from DAVID app>" ,'last_modified':last_modified,"df":david_results["df"],"pa":cp_pa, 'filename2':None, "df_ge": "none"} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data=encode_session_app(session_data["session_data"])
        session["session_data"]=session_data
        return  dcc.Location(pathname=f'{PAGE_PREFIX}/cellplot/', id="index"), None, None, None, dash.no_update, dash.no_update,None, None


    try:
        fig=None
        david_results=run_david_and_cache(pa, cache)
        df = pd.read_json(david_results["df"]) 
        # truncate to two decimal points were appropriate

        # print(df.columns.tolist())
        # df["%"]=df["%"].apply( lambda x: round(x, 2) )
        table_headers=df.columns.tolist()
        for col in ["%","Fold Enrichment"]:
            df[col]=df[col].apply(lambda x: "{0:.2f}".format(float(x)))
        for col in ["PValue","Bonferroni","Benjamini","FDR"]:
            df[col]=df[col].apply(lambda x: '{:.2e}'.format(float(x)))
        for col in ["Genes"]+table_headers[13:]:
            df[col]=df[col].apply(lambda x: str(x)[:40]+"..")

        fig=make_table(df, "david_results")

        return fig, None, None, None,  download_buttons_style_show, download_buttons_style_show, None, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"david")
        return dash.no_update, toast, session_data, tb_str, download_buttons_style_hide, download_buttons_style_hide,  None, None


@dashapp.callback(
    Output('excel-filename-modal', 'is_open'),
    [ Input('save-excel-btn',"n_clicks"),Input("excel-filename-download", "n_clicks")],
    [ State("excel-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_excel_filename(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output('export-filename-modal', 'is_open'),
    [ Input('export-session-btn',"n_clicks"),Input("export-filename-download", "n_clicks")],
    [ State("export-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_export_filename(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output( { 'type': 'collapse-dynamic-card', 'index': MATCH }, "is_open"),
    Input( { 'type': 'dynamic-card', 'index': MATCH }, "n_clicks"),
    State( { 'type': 'collapse-dynamic-card', 'index': MATCH }, "is_open"),
    prevent_initial_call=True
)
def toggle_accordion(n, is_open):
    return not is_open

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

        ask_for_help(tb_str,current_user, "david", session_data)

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