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
from pyflaski.gseaplot import make_figure, figure_defaults
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
from time import sleep


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("gseaplot",url_base_pathname=f'{PAGE_PREFIX}/gseaplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
            make_navbar_logged("GSEA plot",current_user),
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
                dbc.Row(
                    [
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("x values"),
                                    dcc.Dropdown( placeholder="x values", id='xvals', multi=False)
                                ],
                            # ),
                            width=6,
                            style={"padding-right":"4px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("y values" ),
                                    dcc.Dropdown( placeholder="y values", id='yvals', multi=False)
                                ],
                            # ),
                            width=6,
                            style={"padding-left":"4px"}
                        ),
                        # dbc.Col(
                        #     # dbc.FormGroup(
                        #         [
                        #             dbc.Label("Labels"),
                        #             dcc.Dropdown( placeholder="labels", id='groups_value', multi=False)
                        #         ],
                        #     # ),
                        #     width=4,
                        #     style={"padding-left":"4px"}
                        # ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                html.Div(id="labels-section"),
                # dbc.FormGroup(
                #     [
                #         dbc.Col( 
                #             dbc.Label("Labels", style={"margin-top":"5px"}),
                #             width=2   
                #         ),
                #         dbc.Col(
                #             dcc.Dropdown( placeholder="labels", id='fixed_labels', multi=True),
                #             width=10
                #         )
                #     ],
                #     row=True
                # ),
                # dcc.Input(value="labels_card", id="pull_test" ), 
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
                                    dbc.Row(
                                        [

                                            dbc.Label("Width",html_for="fig_width", style={"margin-top":"10px","width":"64px"}), #"height":"35px",
                                            dbc.Col(
                                                dcc.Input(id='fig_width', value = pa['fig_width'], placeholder="eg. 600", type='text', style={"height":"35px","width":"100%"}),
                                                style={"margin-right":"5px"}
                                            ),
                                            dbc.Label("Height", html_for="fig_height",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"right"}),
                                            dbc.Col(
                                                dcc.Input(id='fig_height', value = pa["fig_height"], placeholder="eg. 600", type='text',style={"height":"35px","width":"100%"}  ) ,
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
                                            dbc.Label("size",html_for="titles",width="auto", style={"text-align":"right","margin-left":"5px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["titles"],placeholder="size", id='titles', multi=False, clearable=False, style={"width":"55px"}),
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
                                dbc.Button( "Axes", color="black", id={'type':"dynamic-card","index":"axes"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("x label",html_for='xlabel',width=2),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xlabel"],id='xlabel', placeholder="x label", type='text',style=card_input_style),
                                                    width=6
                                                ),
                                                dbc.Label("size",html_for='xlabels',width=2,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["xlabels"], placeholder="size", id='xlabels', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("y label",html_for='ylabel',width=2),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ylabel"] ,id='ylabel', placeholder="y label", type='text', style=card_input_style) ,
                                                    width=6,
                                                ),
                                                dbc.Label("size",html_for='ylabels',width=2,style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["title_size"]),value=pa["ylabels"],placeholder="size", id='ylabels', multi=False, clearable=False,style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",

                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Axis:"),
                                                style={"textAlign":"left","padding-right":"2px"},
                                                # width=1
                                            ),
                                            dbc.Col(
                                                dbc.Label("left",html_for="left_axis"),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                # width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'left_axis'} ], value=pa["left_axis"], id='left_axis', style={"height":"35px"} ),
                                                # width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("right",html_for="right_axis"),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                # width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'right_axis'} ], value=pa["right_axis"], id='right_axis', style={"height":"35px"} ),
                                                # width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("upper",html_for="upper_axis"),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                # width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'upper_axis'} ], value=pa["upper_axis"], id='upper_axis', style={"height":"35px"} ),
                                                # width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("lower",html_for="lower_axis"),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                # width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'lower_axis'} ], value=pa["lower_axis"], id='lower_axis', style={"height":"35px"} ),
                                                # width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Axis width",width="auto"),
                                                dbc.Col(
                                                    dcc.Input(value=pa["axis_line_width"], id='axis_line_width', placeholder="width", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                    ############################################
                                        dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Ticks:"),
                                                style={"textAlign":"left","padding-right":"2px", "margin-top":"10px"},
                                                width=2
                                            ),
                                            dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("X",html_for="tick_x_axis"),
                                                style={"textAlign":"right","padding-right":"2px", "margin-top":"10px"},
                                                width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'tick_x_axis'} ], value=pa["tick_x_axis"], id='tick_x_axis', style={"height":"35px", "margin-top":"6px"} ),
                                                width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                            dbc.Label("",width=3),
                                            dbc.Col(
                                                dbc.Label("Y",html_for="tick_y_axis"),
                                                style={"textAlign":"right","padding-right":"2px", "margin-top":"10px"},
                                                width=1
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'tick_y_axis'} ], value=pa["tick_y_axis"], id='tick_y_axis', style={"height":"35px", "margin-top":"6px"} ),
                                                width=1
                                                # className="me-3",
                                                # width=5
                                            ),
                                        ],
                                        className="g-1",
                                    ),

                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label(""),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("length",html_for='ticks_length',style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ticks_length"], id='ticks_length', placeholder="length", type='text',style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("direction",html_for='ticks_direction_value',style={"margin-top":"5px"}), # style={"textAlign":"right","padding-right":"2px"}
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["ticks_direction"]), value=pa["ticks_direction_value"], id="ticks_direction_value",placeholder="direction", multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("x ticks", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("font size", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xticks_fontsize"], id='xticks_fontsize', placeholder="size", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("rotation", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xticks_rotation"], id='xticks_rotation', placeholder="rotation", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("y ticks", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("font size", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yticks_fontsize"],id='yticks_fontsize', placeholder="size", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("rotation", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yticks_rotation"],id='yticks_rotation', placeholder="rotation", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("x limits", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("lower", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='x_lower_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='x_upper_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("y limits", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("lower", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='y_lower_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='y_upper_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("N ticks", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("x-axis", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='maxxticks', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("y-axis", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='maxyticks', placeholder="value", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Grid:", html_for="grid_value",style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("type", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid"]), value=pa["grid_value"], id='grid_value', multi=False, style=card_input_style ),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("width", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["grid_linewidth"],id='grid_linewidth', placeholder="value", type='text', style=card_input_style ),
                                                    width=3,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################  PICK UP HERE DOING THE GRID COLOR ROW AS THE TICKS LENGTH AND DIRECTION ABOVE
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("color", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"left","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid_colors"]), value=pa["grid_color_value"] ,placeholder="select", id='grid_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=5
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='grid_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    # style={"padding-left":"4px"}
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 

                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"axes"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px", "padding":"0px", "margin":"0px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Lines", color="black", id={'type':"dynamic-card","index":"marker"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("GSEA Line"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("line width",html_for='gsea_linewidth',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linewidths"]), value=pa["gsea_linewidth"], id='gsea_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label(""),
                                                    width=2
                                                ),                                                
                                                dbc.Label("line style",html_for='gsea_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linestyle"]), value=pa["gsea_linestyle_value"], id='gsea_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("line color",html_for='gsea_colors',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_colors"]), value=pa["gseacolor"], id='gseacolor', multi=False, clearable=False, style=card_input_style),
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='gseacolor_write', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("Gene Ticks"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("tick size",html_for='gene_linewidth',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gene_linewidths"]), value=pa["gene_linewidth"], id='gene_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label(""),
                                                    width=2
                                                ),                                                
                                                # dbc.Label("line style",html_for='gene_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                # dbc.Col(
                                                #     dcc.Dropdown( options=make_options(pa["gene_linestyle"]), value=pa["gene_linestyle_value"], id='gene_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                #     width=2
                                                # )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("line color",html_for='genecolor',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gene_colors"]), value=pa["genecolor"], id='genecolor', multi=False, clearable=False, style=card_input_style),
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='genecolor_write', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("Center Line"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("at",html_for='centerline',width=1),
                                                dbc.Col(
                                                    dcc.Input(value=pa["centerline"],id='centerline', type='text', style=card_input_style ),
                                                    width=2,
                                                ),
                                                dbc.Label("width",html_for='center_linewidth',width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linewidths"]), value=pa["center_linewidth"], id='center_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("style",html_for='center_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["center_linestyle"]), value=pa["center_linestyle_value"], id='center_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("color",html_for='center_color_value',width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["center_colors"]), value=pa["center_color_value"], id='center_color_value', multi=False, clearable=False, style=card_input_style),
                                                    width=5
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='center_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("Maximum Line"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("at",html_for='hline1',width=1),
                                                dbc.Col(
                                                    dcc.Input(value=pa["hline1"],id='hline1', type='text', style=card_input_style ),
                                                    width=2,
                                                ),
                                                dbc.Label("width",html_for='hline1_linewidth',width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linewidths"]), value=pa["hline1_linewidth"], id='hline1_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("style",html_for='hline1_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["hline1_linestyle"]), value=pa["hline1_linestyle_value"], id='hline1_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("color",html_for='hline1_color_value',width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["hline1_colors"]), value=pa["hline1_color_value"], id='hline1_color_value', multi=False, clearable=False, style=card_input_style),
                                                    width=5
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='hline1_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("Minimum Line"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("at",html_for='hline2',width=1),
                                                dbc.Col(
                                                    dcc.Input(value=pa["hline2"],id='hline2', type='text', style=card_input_style ),
                                                    width=2,
                                                ),
                                                dbc.Label("width",html_for='hline2_linewidth',width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linewidths"]), value=pa["hline2_linewidth"], id='hline2_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("style",html_for='hline2_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["hline2_linestyle"]), value=pa["hline2_linestyle_value"], id='hline2_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("color",html_for='hline2_color_value',width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["hline2_colors"]), value=pa["hline2_color_value"], id='hline2_color_value', multi=False, clearable=False, style=card_input_style),
                                                    width=5
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='hline2_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################
                                        dbc.Row(
                                                dbc.Label("Vertical Line"), #"height":"35px",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("at",html_for='vline',width=1),
                                                dbc.Col(
                                                    dcc.Input(value=pa["vline"],id='vline', type='text', style=card_input_style ),
                                                    width=2,
                                                ),
                                                dbc.Label("width",html_for='vline_linewidth',width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["gsea_linewidths"]), value=pa["vline_linewidth"], id='vline_linewidth', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("style",html_for='vline_linestyle_value',width=3,style={ "textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["vline_linestyle"]), value=pa["vline_linestyle_value"], id='vline_linestyle_value', multi=False, clearable=False, style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("color",html_for='vline_color_value',width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["vline_colors"]), value=pa["vline_color_value"], id='vline_color_value', multi=False, clearable=False, style=card_input_style),
                                                    width=5
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='vline_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=5,
                                                    style = {"padding-left": "4px"}
                                                )
                                            ],
                                            className="g-1",
                                        ),

                                        ############################################ 

                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"marker"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px", "padding":"0px", "margin":"0px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Labels", color="black", id={'type':"dynamic-card","index":"labels"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Labels col.",html_for='labels_col_value',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( placeholder="select a column..", id='labels_col_value', multi=False, style=card_input_style ),
                                                    width=9
                                                    # dcc.Input(id='labels_col_value', placeholder=, type='text', style=card_input_style ) ,
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [   
                                                dbc.Label("Y-position",html_for='labels_ypos',width=3),
                                                dbc.Col(
                                                    dcc.Input(value=pa["labels_ypos"],id='labels_ypos', type='text', style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Label("angle",html_for='label_angle',width=3, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["label_angle"],id='label_angle', type='text', style=card_input_style ) ,
                                                    width=3
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [   
                                                dbc.Label("font size",html_for='labels_font_size',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["title_size"]), value=pa["labels_font_size"],id='labels_font_size', placeholder="size", style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Label("color",html_for='labels_font_color_value',width=3, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["labels_font_color"]), value=pa["labels_font_color_value"], placeholder="color", id='labels_font_color_value', multi=False,clearable=False, style=card_input_style ),
                                                    width=3
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("arrows",html_for='labels_arrows_value',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["labels_arrows"]),value=None, placeholder="type", id='labels_arrows_value', multi=False, style=card_input_style ),
                                                    width=3,
                                                ),
                                                dbc.Label("color",html_for='labels_colors_value',width=3,style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["labels_colors"]), value=pa["labels_colors_value"], placeholder="color", id='labels_colors_value', multi=False, clearable=False,style=card_input_style ),
                                                    width=3,
                                                )
                                            ],
                                        className="g-1",
                                        )   
                                        ############################################                                
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"labels"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                )
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
                            dcc.Loading(id="loading-stored-file", children= html.Div(id='stored-file'), style={"height":"100%"}),
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
                                    html.Div( id="toast-update_labels_field"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"update_labels_field" }), 
                                    html.Div( id="toast-generate_markers" ),
                                    dcc.Store( id={ "type":"traceback", "index":"generate_markers" }), 
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
                                    dcc.Input(id='pdf-filename', value="gseaplot.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="gseaplot.json", type='text', style={"width":"100%"})
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
    Output('stored-file', 'children'),
    Input('session-id', 'data'))
def read_session_redis(session_id):
    if "session_data" in list( session.keys() )  :
        imp=session["session_data"]
        del(session["session_data"])
        sleep(3)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"], None
    else:
        return dash.no_update, dash.no_update, dash.no_update, None

read_input_updates=[
    'fig_width', 
    'fig_height', 
    'title', 
    'titles', 
    'xlabel', 
    'xlabels', 
    'ylabel', 
    'ylabels', 
    'left_axis', 
    'right_axis', 
    'upper_axis', 
    'lower_axis', 
    'axis_line_width', 
    'tick_x_axis', 
    'tick_y_axis', 
    'ticks_length', 
    'ticks_direction_value', 
    'xticks_fontsize', 
    'xticks_rotation', 
    'yticks_fontsize', 
    'yticks_rotation', 
    'x_lower_limit', 
    'x_upper_limit', 
    'y_lower_limit', 
    'y_upper_limit', 
    'maxxticks', 
    'maxyticks', 
    'grid_value', 
    'grid_linewidth', 
    'grid_color_value', 
    'grid_color_text', 
    'gsea_linewidth', 
    'gsea_linestyle_value', 
    'gseacolor', 
    'gseacolor_write', 
    'gene_linewidth', 
    #'gene_linestyle_value', 
    'genecolor', 
    'genecolor_write', 
    'centerline', 
    'center_linewidth', 
    'center_linestyle_value', 
    'center_color_value', 
    'center_color_text', 
    'hline1', 
    'hline1_linewidth', 
    'hline1_linestyle_value', 
    'hline1_color_value', 
    'hline1_color_text', 
    'hline2', 
    'hline2_linewidth', 
    'hline2_linestyle_value', 
    'hline2_color_value', 
    'hline2_color_text', 
    'vline', 
    'vline_linewidth', 
    'vline_linestyle_value', 
    'vline_color_value', 
    'vline_color_text', 
    'labels_col_value', 
    'labels_ypos', 
    'label_angle', 
    'labels_font_size', 
    'labels_font_color_value',    
    'labels_arrows_value',    
    'labels_colors_value',    
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ Output('xvals', 'options'),
    Output('yvals', 'options'),
    Output('labels_col_value', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('xvals', 'value'),
    Output('yvals', 'value')] + read_input_updates_outputs ,
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename,last_modified,session_id):
    if not filename :
        raise dash.exceptions.PreventUpdate

    pa_outputs=[ dash.no_update for k in  read_input_updates ]
    try:
        if filename.split(".")[-1] == "json":
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "gseaplot")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            xvals=app_data['pa']["xvals"]
            yvals=app_data['pa']["yvals"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"gseaplot")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            xvals=cols[0]
            yvals=cols[1]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [ cols_, cols_, cols_, upload_text, None, None,  xvals, yvals] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"gseaplot")
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs
   

@dashapp.callback( 
    Output('labels-section', 'children'),
    Output('toast-update_labels_field','children'),
    Output({ "type":"traceback", "index":"update_labels_field" },'data'),
    Output('update_labels_field-import', 'data'),
    Input('session-id','data'),
    Input('labels_col_value','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('update_labels_field-import', 'data'),
)
def update_labels_field(session_id,col,contents,filename,last_modified,update_labels_field_import):
    try:
        if col:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"gseaplot")
            labels=df[[col]].drop_duplicates()[col].tolist()
            labels_=make_options(labels)

            if ( filename.split(".")[-1] == "json" ) and ( not update_labels_field_import ) :
                app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "gseaplot")
                fixed_labels=app_data['pa']["fixed_labels"]
                update_labels_field_import=True
            else:
                fixed_labels=[]

            labels_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Labels", width=2),
                        dbc.Col(
                            dcc.Dropdown( options=labels_, value=fixed_labels,placeholder="labels", id='fixed_labels', multi=True),
                            width=10
                        )
                    ],
                    className="g-1",
                    style={"margin-top":"2px"}
                )
            )
        else:
            labels_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Labels", width=2),
                        dbc.Col(
                            dcc.Dropdown( placeholder="labels", id='fixed_labels', multi=True),
                            width=10
                        )
                    ],
                    # row=True,
                    className="g-1",
                    style= {'display': 'none',"margin-top":"2px"}
                )
            )

        return labels_section, None, None, update_labels_field_import
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem updating the labels field.","update_labels_field", e, current_user,"gseaplot")
        return dash.no_update, toast, tb_str, dash.no_update


states=[State('xvals', 'value'),
    State('yvals', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('title', 'value'),
    State('titles', 'value'),
    State('xlabel', 'value'),
    State('xlabels', 'value'),
    State('ylabel', 'value'),
    State('ylabels', 'value'),
    State('left_axis', 'value'),
    State('right_axis', 'value'),
    State('upper_axis', 'value'),
    State('lower_axis', 'value'),
    State('axis_line_width', 'value'),
    State('tick_x_axis', 'value'),
    State('tick_y_axis', 'value'),
    State('ticks_length', 'value'),
    State('ticks_direction_value', 'value'),
    State('xticks_fontsize', 'value'),
    State('xticks_rotation', 'value'),
    State('yticks_fontsize', 'value'),
    State('yticks_rotation', 'value'),
    State('x_lower_limit', 'value'),
    State('x_upper_limit', 'value'),
    State('y_lower_limit', 'value'),
    State('y_upper_limit', 'value'),
    State('maxxticks', 'value'),
    State('maxyticks', 'value'),
    State('grid_value', 'value'),
    State('grid_linewidth', 'value'),
    State('grid_color_value', 'value'),
    State('grid_color_text', 'value'),
    State('gsea_linewidth', 'value'),
    State('gsea_linestyle_value', 'value'),
    State('gseacolor', 'value'),
    State('gseacolor_write', 'value'),
    State('gene_linewidth', 'value'),
    #State('gene_linestyle_value', 'value'),
    State('genecolor', 'value'),
    State('genecolor_write', 'value'),
    State('centerline', 'value'),
    State('center_linewidth', 'value'),
    State('center_linestyle_value', 'value'),
    State('center_color_value', 'value'),
    State('center_color_text', 'value'),
    State('hline1', 'value'),
    State('hline1_linewidth', 'value'),
    State('hline1_linestyle_value', 'value'),
    State('hline1_color_value', 'value'),
    State('hline1_color_text', 'value'),
    State('hline2', 'value'),
    State('hline2_linewidth', 'value'),
    State('hline2_linestyle_value', 'value'),
    State('hline2_color_value', 'value'),
    State('hline2_color_text', 'value'),
    State('vline', 'value'),
    State('vline_linewidth', 'value'),
    State('vline_linestyle_value', 'value'),
    State('vline_color_value', 'value'),
    State('vline_color_text', 'value'),
    State('labels_col_value', 'value'),
    State('labels_ypos', 'value'),
    State('label_angle', 'value'),
    State('labels_font_size', 'value'),
    State('labels_font_color_value', 'value'),
    State('labels_arrows_value', 'value'),
    State('labels_colors_value', 'value'),
    State('fixed_labels', 'value'),

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
    State('export-filename','value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,session_id,contents,filename,last_modified,export_filename,upload_data_text, *args):
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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"gseaplot")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a


        session_data={ "session_data": {"app": { "gseaplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"gseaplot")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="gseaplot.json"
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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"gseaplot")
            return dash.no_update, toast, None, tb_str, dash.no_update, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    try:
        fig=make_figure(df,pa)
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"gseaplot")
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
        pdf_filename="gseaplot.pdf"
    pdf_filename=secure_filename(pdf_filename)
    if pdf_filename.split(".")[-1] != "pdf":
        pdf_filename=f'{pdf_filename}.pdf'

    ### needs logging
    def write_image(figure, graph=graph):
        ## This section is for bypassing the mathjax bug on inscription on the final plot
        fig=px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])        
        fig.write_image(figure, format="pdf")
        sleep(2)
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

        ask_for_help(tb_str,current_user, "gseaplot", session_data)

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