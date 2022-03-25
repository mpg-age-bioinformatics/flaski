from myapp import app, PAGE_PREFIX
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
from pyflaski.cellplot import make_figure, figure_defaults
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

dashapp = dash.Dash("cellplot",url_base_pathname=f'{PAGE_PREFIX}/cellplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
            make_navbar_logged("Cell plot",current_user),
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
                dbc.Label("DAVID OUTPUT FILE"), #"height":"35px",
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
                dbc.Row(
                    [
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Terms"),
                                    dcc.Dropdown( placeholder="Term Names", id='terms_column', multi=False)
                                ],
                            # ),
                            width=6,
                            style={"padding-right":"4px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Gene Ids" ),
                                    dcc.Dropdown( placeholder="Gene IDs", id='david_gene_ids', multi=False)
                                ],
                            # ),
                            width=6,
                            style={"padding-left":"4px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("X-Axis"),
                                    dcc.Dropdown( placeholder="PValue/ease", id='plotvalue', multi=False)
                                ],
                            # ),
                            width=6,
                            style={"padding-right":"4px", "margin-top":"5px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("" ),
                                    dcc.Checklist(options=[ {'label':'  -Log10(x-axis)', 'value':'log10transform'} ], value=pa["log10transform"], id='log10transform', style={"margin-top":"16px"} ),
                                ],
                            # ),
                            width=6,
                            style={"padding-left":"4px", "margin-top":"5px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                                [
                                    dbc.Label("Categories"),
                                    dcc.Dropdown( placeholder="Category", id='categories_column', multi=False)
                                ],
                            width=6,
                            style={"padding-right":"4px", "margin-top":"5px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                html.Div(id="category-section"),
                dbc.Row(
                    [
                        dbc.Col(
                                [
                                    dbc.Label("Gene Expression"),
                                    dcc.Dropdown( placeholder="log2fc", id='annotation_column_value', multi=False)
                                ],
                            width=6,
                            style={"padding-right":"4px", "margin-top":"5px"}
                        ),
                        dbc.Col(
                                [
                                    dbc.Label("Gene Names"),
                                    dcc.Dropdown( placeholder="genes name", id='annotation2_column_value', multi=False)
                                ],
                            width=6,
                            style={"padding-left":"4px", "margin-top":"5px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                ############################
                dbc.Row([
                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"20px" })
                ],
                className="g-1",
                ),
                ############################
                dbc.Label("GENE EXPRESSION OUTPUT FILE"), #"height":"35px",
                html.Div(
                    dcc.Upload(
                        id='upload-data2',
                        children=html.Div(
                            [ 'Drag and Drop or ',html.A('Select File',id='upload-data2-text') ],
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
                dbc.Row(
                    [
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Gene Ids"),
                                    dcc.Dropdown( placeholder="Gene IDs", id='gene_identifier', multi=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-right":"4px", "margin-top":"5px", "margin-bottom":"10px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Gene Names"),
                                    dcc.Dropdown( placeholder="genes name", id='gene_name', multi=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-left":"2px", "padding-right":"2px", "margin-top":"5px", "margin-bottom":"10px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Gene Expression"),
                                    dcc.Dropdown( placeholder="log2fc", id='expression_values', multi=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-left":"4px", "margin-top":"5px", "margin-bottom":"10px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                ############################
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Figure", color="black", id={'type':"dynamic-card","index":"figure"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                    ## example card body row
                                    # dbc.Row(
                                    #     [

                                    #         dbc.Label("Width", width="auto",style={"margin-right":"2px"}),
                                    #         dbc.Col(
                                    #             dcc.Input(id='width', placeholder="eg. 600", type='text', style=card_input_style),
                                    #             style={"margin-right":"5px"}
                                    #         ),
                                    #         dbc.Label("Height", width="auto",style={"margin-right":"2px", "margin-left":"5px"}),
                                    #         dbc.Col(
                                    #             dcc.Input(id='height', placeholder="eg. 600", type='text',style=card_input_style  ) ,
                                    #         ),
        
                                    #     ],
                                    #     className="g-0",
                                    # ),
                                    ## end of example card body row
                                    dbc.Row(
                                        [

                                            dbc.Label("Width",html_for="width", style={"margin-top":"10px","width":"64px"}), #"height":"35px",
                                            dbc.Col(
                                                dcc.Input(id='width', value=pa["width"], placeholder="eg. 600", type='text', style={"height":"35px","width":"100%"}),
                                                style={"margin-right":"5px"}
                                            ),
                                            dbc.Label("Height", html_for="height",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"right"}),
                                            dbc.Col(
                                                dcc.Input(id='height', value = pa["height"], placeholder="eg. 600", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
        
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Title",width="auto",html_for="title",style={"margin-top":"0px","width":"64px"}), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder="title", type='text', style={"height":"35px","min-width":"169px","width":"100%"} ) ,
                                                style={"margin-right":"5px"},
                                            ),
                                            dbc.Label("size",html_for="title_font_size",width="auto", style={"text-align":"right","margin-left":"5px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["title_font_size"],placeholder="size", id='title_font_size', style={"width":"55px"}),
                                            )
                                        ],
                                        className="g-1",
                                        justify="between"
                                    ), 
                                    ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"figure"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Plot", color="black", id={'type':"dynamic-card","index":"plot"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        ############################
                                        dbc.Row(
                                            [
                                            # dbc.Col(
                                            #     dbc.Label(,html_for="write_n_terms"),
                                            #     style={"textAlign":"left","padding-right":"2px"},
                                            #     width=7
                                            # ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label': " Annotation bars with n. Terms", 'value':'write_n_terms'} ], value=pa["write_n_terms"], id='write_n_terms', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=8
                                                # className="me-3",
                                                # width=5
                                            ),
                                                dbc.Col(
                                                    dbc.Label("size", html_for="annotation_size",style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px", 'margin-top':"10px"}
                                                ),
                                                dbc.Col(
                                                dcc.Input(value=pa["annotation_size"],placeholder="size", id='annotation_size', style=card_input_style),
                                                    width =2
                                                ),
            
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label': " Reverse rows order", 'value':'reverse_y_order'} ], value=pa["reverse_y_order"], id='reverse_y_order', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=8
                                                # className="me-3",
                                                # width=5
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                            dbc.Col(
                                                dbc.Label("CMAP",html_for="color_scale_value", style={"margin-top":"5px"}),
                                                style={"textAlign":"left","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["color_scale"]), value=pa["color_scale_value"], placeholder="color_scale_value", id='color_scale_value', multi=False, clearable=False, style=card_input_style),
                                                width=6
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label': " reverse", 'value':'reverse_color_scale'} ], value=pa["reverse_color_scale"], id='reverse_color_scale', style={"height":"35px", } ),
                                                style={"textAlign":"right","padding-right":"2px", 'margin-top':"10px"},
                                                width=4
                                                # className="me-3",
                                                # width=5
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Set the continuous color midpoint", html_for="color_continuous_midpoint",style={"margin-top":"5px"}),
                                                    # width=8,
                                                    style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"}
                                                ),
                                                dbc.Col(
                                                dcc.Input(value=pa["color_continuous_midpoint"],placeholder="", id='color_continuous_midpoint', style=card_input_style),
                                                    # width=4
                                                ),
            
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("... or the color scale percentile (0 - 100)", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"}
                                                ),            
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("lower",html_for="lower_expression_percentile", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["lower_expression_percentile"],id='lower_expression_percentile', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper",html_for="upper_expression_percentile", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["upper_expression_percentile"],id='upper_expression_percentile', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("... or explicitly define your color map", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"}
                                                ),            
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Lower", style={"margin-top":"5px"}),
                                                    style={"textAlign":"center","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Center", style={"margin-top":"5px"}),
                                                    style={"textAlign":"center","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Upper", style={"margin-top":"5px"}),
                                                    style={"textAlign":"center"},
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Value", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["lower_value"],id='lower_value', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["center_value"],id='center_value', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["upper_value"],id='upper_value', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Color", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["lower_color"],id='lower_color', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["center_color"],id='center_color', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["upper_color"],id='upper_color', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Color bar title",html_for="color_bar_title", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["color_bar_title"],id='color_bar_title', placeholder="", type='text', style=card_input_style),
                                                    width=9
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Size",html_for="color_bar_title_font_size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["color_bar_title_font_size"],id='color_bar_title_font_size', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Tick font size",html_for="color_bar_tickfont", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["color_bar_tickfont"],id='color_bar_tickfont', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Width",html_for="color_bar_tickwidth", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["color_bar_tickwidth"],id='color_bar_tickwidth', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Length",html_for="color_bar_ticklen", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["color_bar_ticklen"],id='color_bar_ticklen', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                            dbc.Col(
                                                dbc.Label("Y-Axis line",html_for="yaxis_line", style={"margin-top":"5px"}),
                                                style={"textAlign":"left","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'yaxis_line'} ], value=pa["yaxis_line"], id='yaxis_line', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=5
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("Mirror Line",html_for="rightyaxis_line", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'rightyaxis_line'} ], value=pa["rightyaxis_line"], id='rightyaxis_line', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                            dbc.Col(
                                                dbc.Label("X-Axis line",html_for="xaxis_line", style={"margin-top":"5px"}),
                                                style={"textAlign":"left","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'xaxis_line'} ], value=pa["xaxis_line"], id='xaxis_line', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("position",html_for="xaxis_side", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["xaxis_side_opt"]), value=pa["xaxis_side"], placeholder="xaxis_side", id='xaxis_side', multi=False, clearable=False, style=card_input_style),
                                                width=2
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("Mirror Line",html_for="topxaxis_line", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'topxaxis_line'} ], value=pa["topxaxis_line"], id='topxaxis_line', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Line width",html_for="yaxis_linewidth", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yaxis_linewidth"],id='yaxis_linewidth', placeholder="", type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label(""),
                                                    width=6
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("X-Axis label",html_for="xaxis_label", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_label"],id='xaxis_label', placeholder="", type='text', style=card_input_style),
                                                    width=9
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Y-Axis label",html_for="yaxis_label", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yaxis_label"],id='yaxis_label', placeholder="", type='text', style=card_input_style),
                                                    width=9
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Label font size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dbc.Label("X",html_for="xaxis_label_size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_label_size"],id='xaxis_label_size', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Y",html_for="yaxis_label_size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yaxis_label_size"],id='yaxis_label_size', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Axis font size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dbc.Label("X",html_for="xaxis_font_size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_font_size"],id='xaxis_font_size', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Y",html_for="yaxis_font_size", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yaxis_font_size"],id='yaxis_font_size', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("X-Axis tick", style={"margin-top":"5px"}),
                                                    style={"textAlign":"left","padding-right":"2px"},
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dbc.Label("width",html_for="xaxis_tickwidth", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_tickwidth"],id='xaxis_tickwidth', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("length",html_for="xaxis_ticklen", style={"margin-top":"5px"}),
                                                    style={"textAlign":"right","padding-right":"2px"},
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_ticklen"],id='xaxis_ticklen', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                            dbc.Col(
                                                dcc.Checklist(options=[ {"label":' Grid','value':'grid'} ], value=pa["grid"], id='grid', style={"height":"35px", } ),
                                                style={"textAlign":"left","padding-right":"2px", 'margin-top':"10px"},
                                                width=3
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("N terms to plot",html_for="number_of_terms", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=7
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["number_of_terms"],id='number_of_terms', placeholder="", type='text', style=card_input_style),
                                                width=2
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 

                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"plot"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px", "padding":"0px", "margin":"0px"} 
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
            dcc.Store( id='update_category_field-import'),
            # dcc.Store( id='generate_markers-import'),
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
                                    html.Div( id="toast-update_category_field"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"update_category_field" }), 
                                    # html.Div( id="toast-generate_markers" ),
                                    # dcc.Store( id={ "type":"traceback", "index":"generate_markers" }), 
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
                                    dcc.Input(id='pdf-filename', value="cellplot.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="cellplot.json", type='text', style={"width":"100%"})
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
        from time import sleep
        sleep(2)
        print(imp)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update

read_input_updates=[
    #'terms_column',
    #'david_gene_ids',
    #'plotvalue',
    'log10transform',
    #'categories_column',
    #'categories_to_plot_value',
    #'annotation_column_value',
    #'annotation2_column_value',
    # 'expression_values',
    # 'gene_name',
    'width',
    'height',
    'title',
    'title_font_size',
    'write_n_terms',
    'annotation_size',
    'reverse_y_order',
    'color_scale_value',
    'reverse_color_scale',
    'color_continuous_midpoint',
    'lower_expression_percentile',
    'upper_expression_percentile',
    'lower_value',
    'center_value',
    'upper_value',
    'lower_color',
    'center_color',
    'upper_color',
    'color_bar_title',
    'color_bar_title_font_size',
    'color_bar_tickfont',
    'color_bar_tickwidth',
    'color_bar_ticklen',
    'yaxis_line',
    'rightyaxis_line',
    'xaxis_line',
    'xaxis_side',
    'topxaxis_line',
    'yaxis_linewidth',
    'xaxis_label',
    'yaxis_label',
    'xaxis_label_size',
    'yaxis_label_size',
    'xaxis_font_size',
    'yaxis_font_size',
    'xaxis_tickwidth',
    'xaxis_ticklen',
    'grid',
    'number_of_terms',
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ 
    Output('terms_column', 'options'),
    Output('david_gene_ids', 'options'),
    Output('plotvalue', 'options'),
    Output('categories_column', 'options'),
    Output('annotation_column_value', 'options'),
    Output('annotation2_column_value', 'options'),
    Output('gene_identifier', 'options'),
    Output('expression_values', 'options'),
    Output('gene_name', 'options'),
    Output('upload-data','children'),
    Output('upload-data2','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('terms_column', 'value'),
    Output('david_gene_ids', 'value'),
    Output('plotvalue', 'value'),
    Output('categories_column', 'value'),
    Output('annotation_column_value', 'value'),
    Output('annotation2_column_value', 'value'),
    Output('gene_identifier', 'value'),
    Output('expression_values', 'value'),
    Output('gene_name', 'value'),
    ] + read_input_updates_outputs ,
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    Input('upload-data2', 'contents'),
    State('upload-data2', 'filename'), 
    State('upload-data', 'last_modified'),
    State('upload-data2', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename, contents2, filename2, last_modified, last_modified2,session_id):
    if not filename :
        raise dash.exceptions.PreventUpdate
    read_json=False
    print("Cellplot read input")
    pa_outputs=[ dash.no_update for k in  read_input_updates ]
    try:
        if filename.split(".")[-1] == "json":
            print("parse json")
            read_json=True
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "cellplot")
            #first dataframe
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            # second dataframe
            if app_data["df_ge"] != "none":
                df2=pd.read_json(app_data["df_ge"])
                cols2 = df2.columns.tolist()
                cols2_= make_options(cols2)
            else:
                cols2_="None"
            # rest of data
            filename=app_data["filename"]
            filename2=app_data["filename2"]
            terms_column=app_data['pa']["terms_column"]
            david_gene_ids=app_data['pa']["david_gene_ids"]
            plotvalue=app_data['pa']["plotvalue"]
            categories_column=app_data['pa']["categories_column"]
            annotation_column_value=app_data['pa']["annotation_column_value"]
            annotation2_column_value=app_data['pa']["annotation2_column_value"]
            gene_identifier=app_data['pa']["gene_identifier"]
            expression_values=app_data['pa']["expression_values"]
            gene_name=app_data['pa']["gene_name"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            print("parsing dataframe")
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"cellplot")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            terms_column=cols[1]
            david_gene_ids=cols[5]
            plotvalue=cols[4]
            categories_column=cols[0]
            annotation_column_value=None
            annotation2_column_value=None
            gene_identifier=None
            expression_values=None
            gene_name=None
        
        if not read_json:
            if filename2:
                df2=parse_table(contents2,filename2,last_modified2,current_user.id,cache,"cellplot")
                app_data=dash.no_update
                cols2=df2.columns.tolist()
                cols2_=make_options(cols2)
            else:
                cols2_="None"


        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )
        if filename2:
            upload_text2=html.Div(
                [ html.A(filename2, id='upload-data2-text') ],
                 style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
            )
        else:
            upload_text2=html.Div(
                ['Drag and Drop or ', html.A('Select File', id='upload-data2-text') ],
                 style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
            )
        
        print(filename2)
        print("HERE6")
        return [ cols_, cols_,cols_, cols_, cols_,cols_, cols2_,cols2_,cols2_, upload_text, upload_text2, None, None, \
            terms_column, david_gene_ids, plotvalue, categories_column, annotation_column_value, annotation2_column_value, gene_identifier, expression_values, gene_name ] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"cellplot")
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs
   
@dashapp.callback( 
    Output('category-section', 'children'),
    Output('toast-update_category_field','children'),
    Output({ "type":"traceback", "index":"update_category_field" },'data'),
    Output('update_category_field-import', 'data'),
    Input('session-id','data'),
    Input('categories_column','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('update_category_field-import', 'data'),
)
def update_category_field(session_id,col,contents,filename,last_modified,update_category_field_import):
    try:
        if col:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"cellplot")
            category=df[[col]].drop_duplicates()[col].tolist()
            category_=make_options(category)

            if ( filename.split(".")[-1] == "json" ) and ( not update_category_field_import ) :
                app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "cellplot")
                categories_to_plot_value=app_data['pa']["categories_to_plot_value"]
                update_category_field_import=True
            else:
                categories_to_plot_value=[]


            category_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Categories to plot", width=2),
                        dbc.Col(
                            dcc.Dropdown( options=category_, value=category, id='categories_to_plot_value', multi=True),
                            width=10
                        )
                    ],
                    className="g-1",
                    style={"margin-top":"2px"}
                )
            )
        else:
            category_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Categories to plot", width=2),
                        dbc.Col(
                            dcc.Dropdown( placeholder="category", id='categories_to_plot_value', multi=True),
                            width=10
                        )
                    ],
                    # row=True,
                    className="g-1",
                    style= {'display': 'none',"margin-top":"2px"}
                )
            )

        return category_section, None, None, update_category_field_import
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem updating the category field.","update_category_field", e, current_user,"cellplot")
        return dash.no_update, toast, tb_str, dash.no_update

states=[
    State('terms_column', 'value'),
    State('david_gene_ids', 'value'),
    State('plotvalue', 'value'),
    State('log10transform', 'value'),
    State('categories_column', 'value'),
    State('categories_to_plot_value', 'value'),
    State('annotation_column_value', 'value'),
    State('annotation2_column_value', 'value'),
    State('gene_identifier', 'value'),
    State('expression_values', 'value'),
    State('gene_name', 'value'),
    State('width', 'value'),
    State('height', 'value'),
    State('title', 'value'),
    State('title_font_size', 'value'),
    State('write_n_terms', 'value'),
    State('reverse_y_order', 'value'),
    State('reverse_color_scale', 'value'),
    State('annotation_size', 'value'),
    State('color_scale_value', 'value'),
    State('color_continuous_midpoint', 'value'),
    State('lower_expression_percentile', 'value'),
    State('upper_expression_percentile', 'value'),
    State('lower_value', 'value'),
    State('center_value', 'value'),
    State('upper_value', 'value'),
    State('lower_color', 'value'),
    State('center_color', 'value'),
    State('upper_color', 'value'),
    State('color_bar_title', 'value'),
    State('color_bar_title_font_size', 'value'),
    State('color_bar_tickfont', 'value'),
    State('color_bar_tickwidth', 'value'),
    State('color_bar_ticklen', 'value'),
    State('yaxis_line', 'value'),
    State('rightyaxis_line', 'value'),
    State('xaxis_line', 'value'),
    State('xaxis_side', 'value'),
    State('topxaxis_line', 'value'),
    State('yaxis_linewidth', 'value'),
    State('xaxis_label', 'value'),
    State('yaxis_label', 'value'),
    State('xaxis_label_size', 'value'),
    State('yaxis_label_size', 'value'),
    State('xaxis_font_size', 'value'),
    State('yaxis_font_size', 'value'),
    State('xaxis_tickwidth', 'value'),
    State('xaxis_ticklen', 'value'),
    State('grid', 'value'),
    State('number_of_terms', 'value'),
     ]    

@dashapp.callback( 
    Output('fig-output', 'children'),
    Output( 'toast-make_fig_output','children'),
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
    State('upload-data2', 'contents'),
    State('upload-data2', 'filename'),
    State('upload-data2', 'last_modified'),
    State('export-filename','value'),
    State('upload-data-text', 'children'),
    State('upload-data2-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,session_id,contents,filename,last_modified,contents2,filename2,last_modified2,export_filename,upload_data_text, upload_data2_text, *args):
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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"cellplot")

        if filename.split(".")[-1] == "json":
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "cellplot")
            if app_data["df_ge"] != "none":
                df_ge=pd.read_json(app_data["df_ge"])
            else:
                df_ge="none"
        elif filename2 :
            df_ge=parse_table(contents2,filename2,last_modified2,current_user.id,cache,"cellplot")
        else:
            df_ge = "none"

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a



        df = df.astype(str)
        if filename2:
            session_data={ "session_data": {"app": { "cellplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa, 'filename2':upload_data2_text, "df_ge": df_ge.to_json()} } } }
            session_data["APP_VERSION"]=app.config['APP_VERSION']
        else:
            session_data={ "session_data": {"app": { "cellplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa, 'filename2':upload_data2_text, "df_ge": df_ge} } } }
            session_data["APP_VERSION"]=app.config['APP_VERSION']
            
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"cellplot")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="cellplot.json"
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
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"cellplot")
            return dash.no_update, toast, None, tb_str, dash.no_update, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    try:
        fig=make_figure(df, df_ge, pa)
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
        fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
        fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")

        # changed
        # return fig, None, session_data, None, download_buttons_style_show
        # as session data is no longer required for downloading the figure

        return fig, None, None, None, download_buttons_style_show, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"cellplot")
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
        pdf_filename="cellplot.pdf"
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

        ask_for_help(tb_str,current_user, "cellplot", session_data)

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