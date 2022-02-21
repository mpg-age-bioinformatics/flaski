from myapp import app
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
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

dashapp = dash.Dash("david",url_base_pathname='/david/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
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
                        },
                        multiple=False,
                    ),
                ),
                # dbc.Row(
                #     [
                #         dbc.Col(
                #             # dbc.FormGroup(
                #                 [
                #                     dbc.Label("x values"),
                #                     dcc.Dropdown( placeholder="x values", id='xvals', multi=False)
                #                 ],
                #             # ),
                #             width=4,
                #             style={"padding-right":"4px"}
                #         ),
                #         dbc.Col(
                #             # dbc.FormGroup(
                #                 [
                #                     dbc.Label("y values" ),
                #                     dcc.Dropdown( placeholder="y values", id='yvals', multi=False)
                #                 ],
                #             # ),
                #             width=4,
                #             style={"padding-left":"2px","padding-right":"2px"}
                #         ),
                #         dbc.Col(
                #             # dbc.FormGroup(
                #                 [
                #                     dbc.Label("Groups"),
                #                     dcc.Dropdown( placeholder="groups", id='groups_value', multi=False)
                #                 ],
                #             # ),
                #             width=4,
                #             style={"padding-left":"4px"}
                #         ),
                #     ],
                #     align="start",
                #     justify="betweem",
                #     className="g-0",
                # ),
                ############################
                dbc.Row(
                        dbc.Label("Target Genes"), #"height":"35px",
                ),
                ############################
                dbc.Row(
                    [
                        dbc.Col(
                            dcc.Textarea(value=pa["ids"], id='ids', placeholder="", style={"height":"100px","width":"100%"}),
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
                            dcc.Textarea(value=pa["ids_bg"], id='ids_bg', placeholder="", style={"height":"100px","width":"100%"}),
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                ############################
                dbc.Row([
                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                ],
                className="g-0",
                ),
                ############################
                dbc.Row(
                        dbc.Label("Arguments"), #"height":"35px",
                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                                ],
                                className="g-1",
                                ),
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
                                        dcc.Input(value=pa["user"], id='user',style=card_input_style),
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
            style={ "min-width":"372px","width":"100%"},
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
                                                        html.I(className="fas fas fa-file-pdf"),
                                                        " PDF" 
                                                    ]
                                                ),
                                                id='download-pdf-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id="download-pdf")
                                        ],
                                        id="download-pdf-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display': 'none'} # 'none' / 'inline-block'
                                    )
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
                                    dcc.Input(id='pdf-filename', value="david.pdf", type='text', style={"width":"100%"})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Download", id="pdf-filename-download", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="pdf-filename-modal",
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
        imp=session["session_data"]
        del(session["session_data"])
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update

read_input_updates=[ ]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

# @dashapp.callback( 
#     [ Output('xvals', 'options'),
#     Output('yvals', 'options'),
#     Output('groups_value', 'options'),
#     Output('labels_col_value', 'options'),
#     Output('upload-data','children'),
#     Output('toast-read_input_file','children'),
#     Output({ "type":"traceback", "index":"read_input_file" },'data'),
#     # Output("json-import",'data'),
#     Output('xvals', 'value'),
#     Output('yvals', 'value')] + read_input_updates_outputs ,
#     Input('upload-data', 'contents'),
#     State('upload-data', 'filename'),
#     State('upload-data', 'last_modified'),
#     State('session-id', 'data'),
#     prevent_initial_call=True)
# def read_input_file(contents,filename,last_modified,session_id):
#     if not filename :
#         raise dash.exceptions.PreventUpdate

#     pa_outputs=[ dash.no_update for k in  read_input_updates ]
#     try:
#         if filename.split(".")[-1] == "json":
#             app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "david")
#             df=pd.read_json(app_data["df"])
#             cols=df.columns.tolist()
#             cols_=make_options(cols)
#             filename=app_data["filename"]
#             xvals=app_data['pa']["xvals"]
#             yvals=app_data['pa']["yvals"]

#             pa=app_data["pa"]

#             pa_outputs=[pa[k] for k in  read_input_updates ]

#         else:
#             df=parse_table(contents,filename,last_modified,current_user.id,cache,"david")
#             app_data=dash.no_update
#             cols=df.columns.tolist()
#             cols_=make_options(cols)
#             xvals=cols[0]
#             yvals=cols[1]

#         upload_text=html.Div(
#             [ html.A(filename, id='upload-data-text') ],
#             style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
#         )     
#         return [ cols_, cols_, cols_, cols_, upload_text, None, None,  xvals, yvals] + pa_outputs

#     except Exception as e:
#         tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
#         toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"david")
#         return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs
   

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
    Output('download-pdf-div', 'style'),
    Output('export-session','data'),
    Input("submit-button-state", "n_clicks"),
    Input("export-filename-download","n_clicks"),
    Input("save-session-btn","n_clicks"),
    Input("saveas-session-btn","n_clicks"),
    [ State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('export-filename','value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,session_id,contents,filename,last_modified,export_filename,upload_data_text, *args):
    ## This function can be used for the export, save, and save as by making use of 
    ## Determining which Input has fired with dash.callback_context
    ## in https://dash.plotly.com/advanced-callbacks
    ctx = dash.callback_context
    print("HERE1")
    if not ctx.triggered:
        button_id = 'No clicks yet'
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    download_buttons_style_show={"max-width":"150px","width":"100%","margin":"4px",'display': 'inline-block'} 
    download_buttons_style_hide={"max-width":"150px","width":"100%","margin":"4px",'display': 'none'} 
    try:
        input_names = [item.component_id for item in states]

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a

        session_data={ "session_data": {"app": { "david": {"filename":upload_data_text ,'last_modified':last_modified,"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"david")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    try:
        user=pa["user"]
        print(user)
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"david")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

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

        return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "save-session-btn" :
        try:
            if filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None, dash.no_update, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname="/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"david")
            return dash.no_update, toast, None, tb_str, dash.no_update, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname="/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    try:
        fig=None
        david_results=run_david(pa)
        print("HERE3")
        # fig=make_figure(df,pa)
        # import plotly.graph_objects as go
        # fig = go.Figure( )
        # fig.update_layout( )
        # fig.add_trace(go.Scatter(x=[1,2,3,4], y=[2,3,4,8]))
        # fig.update_layout(
        #         title={
        #             'text': "Demo plotly title",
        #             'xanchor': 'left',
        #             'yanchor': 'top' ,
        #             "font": {"size": 25, "color":"black"  } } )
        # fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
        # fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")

        # changed
        # return fig, None, session_data, None, download_buttons_style_show
        # as session data is no longer required for downloading the figure

        return fig, None, None, None, download_buttons_style_show, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"david")
        return dash.no_update, toast, session_data, tb_str, download_buttons_style_hide, None

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
    Output('pdf-filename-modal', 'is_open'),
    [ Input('download-pdf-btn',"n_clicks"),Input("pdf-filename-download", "n_clicks")],
    [ State("pdf-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_pdf_filename(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output('download-pdf', 'data'),
    Input('pdf-filename-download',"n_clicks"),
    State('graph', 'figure'),
    State("pdf-filename", "value"),
    prevent_initial_call=True
)
def download_pdf(n_clicks,graph, pdf_filename):
    if not pdf_filename:
        pdf_filename="david.pdf"
    pdf_filename=secure_filename(pdf_filename)
    if pdf_filename.split(".")[-1] != "pdf":
        pdf_filename=f'{pdf_filename}.pdf'

    ### needs logging
    def write_image(figure, graph=graph):
        ## This section is for bypassing the mathjax bug on inscription on the final plot
        fig=px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])        
        fig.write_image(figure, format="pdf")
        time.sleep(2)
        ## 
        fig=go.Figure(graph)
        fig.write_image(figure, format="pdf")
    return dcc.send_bytes(write_image, pdf_filename)

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