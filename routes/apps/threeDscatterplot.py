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
from pyflaski.threeDscatterplot import make_figure, figure_defaults
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
from myapp import db
from myapp.models import UserLogging
from time import sleep

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("threeDscatterplot",url_base_pathname=f'{PAGE_PREFIX}/threeDscatterplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="3D Scatter plot" , assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit threeDscatterplot")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("3D Scatter plot",current_user),
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
                                    dcc.Dropdown( placeholder="x values", id='xvals', multi=False, clearable=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-right":"4px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("y values" ),
                                    dcc.Dropdown( placeholder="y values", id='yvals', multi=False, clearable=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-left":"2px","padding-right":"2px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("z values" ),
                                    dcc.Dropdown( placeholder="z values", id='zvals', multi=False, clearable=False)
                                ],
                            # ),
                            width=4,
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
                                    dbc.Label("Groups"),
                                    dcc.Dropdown( placeholder="groups", id='groups_value', multi=False)
                                ],
                            # ),
                            width=12,
                            style={"padding-top":"10px"}
                        ),
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
                                                dcc.Input(id='fig_width', placeholder="eg. 600", type='text', style={"height":"35px","width":"100%"}),
                                                style={"margin-right":"5px"}
                                            ),
                                            dbc.Label("Height", html_for="fig_height",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"right"}),
                                            dbc.Col(
                                                dcc.Input(id='fig_height', placeholder="eg. 600", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
        
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Title",width=3,html_for="title",style={"margin-top":"0px"}), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder="title", type='text', style=card_input_style ) ,
                                                width=5,
                                            ),
                                            dbc.Label("size",html_for="titles",width=2, style={"text-align":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["titles"],placeholder="size", id='titles', multi=False, clearable=False, style=card_input_style),
                                                width=2,
                                            )
                                        ],
                                        className="g-1",
                                        justify="between"
                                    ),                                
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Legend",html_for="show_legend", style={"margin-top":"10px","width":"64px"}),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' show legend', 'value':'show_legend'} ], value=pa["show_legend"], id='show_legend', style={"margin-top":"6px","height":"35px"} ),
                                                # className="me-3",
                                                # width=5
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Legend Title",width=3,html_for="legend_title",style={"margin-top":"0px"}), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_title"],id='legend_title', placeholder="", type='legend_title', style=card_input_style ) ,
                                                width = 5,
                                            ),
                                            dbc.Label("size",html_for="legend_font_size",width=2, style={"text-align":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["title_size"]), value=pa["legend_font_size"],placeholder="size", id='legend_font_size', multi=False, clearable=False, style=card_input_style),
                                                width=2,
                                            )
                                        ],
                                        className="g-1",
                                        justify="between"
                                    ),                                
                                    ############################
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
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("z label",html_for='zlabel',width=2),
                                                dbc.Col(
                                                    dcc.Input(value=pa["zlabel"] ,id='zlabel', placeholder="z label", type='text', style=card_input_style) ,
                                                    width=6,
                                                ),
                                                dbc.Label("size",html_for='zlabels',width=2,style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["title_size"]),value=pa["zlabels"],placeholder="size", id='zlabels', multi=False, clearable=False,style=card_input_style),
                                                    width=2
                                                )
                                            ],
                                            className="g-1",

                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Axis:",html_for="show_axis", width=2),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X-Axis   ', 'value': 'x_axis'},
                                                            {'label': ' Y-Axis   ', 'value': 'y_axis'},
                                                            {'label': ' Z-Axis   ', 'value': 'z_axis'}
                                                        ],
                                                        value=pa["show_axis"],
                                                        labelStyle={'display': 'inline-block',"margin-right":"10px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"16px"},
                                                        id="show_axis"
                                                    ),
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Mirror:",html_for="show_mirror_axis", width=2),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X-Axis   ', 'value': 'mirror_x_axis'},
                                                            {'label': ' Y-Axis   ', 'value': 'mirror_y_axis'},
                                                            {'label': ' Z-Axis   ', 'value': 'mirror_z_axis'}
                                                        ],
                                                        value=pa["show_mirror_axis"],
                                                        labelStyle={'display': 'inline-block',"margin-right":"10px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"16px"},
                                                        id="show_mirror_axis"
                                                    ),
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("",width=2),
                                                dbc.Label("Line width",width="auto"),
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
                                                dbc.Label("Tick Labels:",html_for="tick_axis",width=4),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X   ', 'value': 'x_tick_labels'},
                                                            {'label': ' Y   ', 'value': 'y_tick_labels'},
                                                            {'label': ' Z   ', 'value': 'z_tick_labels'},
                                                        ],
                                                        value=pa["tick_axis"],
                                                        labelStyle={'display': 'inline-block',"margin-right":"10px"},
                                                        style={"height":"35px","margin-top":"16px"},
                                                        id="tick_axis"
                                                    ),
                                                )
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
                                                    dbc.Label("z ticks", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("font size", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["zticks_fontsize"],id='zticks_fontsize', placeholder="size", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("rotation", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["zticks_rotation"],id='zticks_rotation', placeholder="rotation", type='text', style=card_input_style ) ,
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
                                                    dcc.Input(id='x_lower_limit', placeholder="", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='x_upper_limit', placeholder="", type='text', style=card_input_style ) ,
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
                                                    dcc.Input(id='y_lower_limit', placeholder="", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='y_upper_limit', placeholder="", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("z limits", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("lower", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='z_lower_limit', placeholder="", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("upper", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='z_upper_limit', placeholder="", type='text', style=card_input_style ) ,
                                                    width=2
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Max ticks for each axis", style={"margin-top":"5px"}),
                                                ),
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("X", style={"margin-top":"5px"}),
                                                    width=1,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='maxxticks', placeholder="", type='text', style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Y", style={"margin-top":"5px"}),
                                                    width=1,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='maxyticks', placeholder="", type='text', style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Z", style={"margin-top":"5px"}),
                                                    width=1,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='maxzticks', placeholder="", type='text', style=card_input_style ) ,
                                                    width=3
                                                )
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Background color for each axis", style={"margin-top":"5px"}),
                                                ),
                                            ],
                                            className="g-0",
                                        ),
                                        ############################################  
                                        dbc.Row(
                                            [
                                                dbc.Label("X",width=1),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["x_axis_background_colors"]), value=pa["x_axis_background_color"] , id='x_axis_background_color', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='x_axis_background_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=7
                                                    # style={"padding-left":"4px"}
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################  
                                        dbc.Row(
                                            [
                                                dbc.Label("Y",width=1),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["y_axis_background_colors"]), value=pa["y_axis_background_color"] , id='y_axis_background_color', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='y_axis_background_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=7
                                                    # style={"padding-left":"4px"}
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################  
                                        dbc.Row(
                                            [
                                                dbc.Label("Z",width=1),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["z_axis_background_colors"]), value=pa["z_axis_background_color"] , id='z_axis_background_color', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=4
                                                ),
                                                dbc.Col(
                                                    dcc.Input(id='z_axis_background_color_text', placeholder=".. or, write color name", type='text', style=card_input_style),
                                                    width=7
                                                    # style={"padding-left":"4px"}
                                                ),
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
                                                    dbc.Label("Grid:", html_for="grid_value",style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("type", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid"]), value=pa['grid_value'], id='grid_value', multi=False, style=card_input_style ),
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
                                        ############################################  
                                        dbc.Row(
                                            [
                                                dbc.Label("",width=2),
                                                dbc.Col(
                                                    dbc.Label("color", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid_colors"]), value=pa["grid_color_value"] ,placeholder="select", id='grid_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=3
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
                                dbc.Button( "Reference Planes", color="black", id={'type':"dynamic-card","index":"planes"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        # ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("X-Axis plane",style={'font-weight': 'bold'}, width = 4),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("",width=4),
                                                dbc.Label("at:",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='x_axis_plane', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("Opacity",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='x_axis_plane_color_opacity', value=pa["x_axis_plane_color_opacity"], type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                            dbc.Label("X-CMAP",width=3, style = {"textAlign":"left"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["plane_colors"]), value=pa["x_axis_plane_color_value"] , id='x_axis_plane_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=5
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' reverse', 'value':'x_axis_reverse_color_scale'} ], value=pa["x_axis_reverse_color_scale"], id='x_axis_reverse_color_scale', style={"margin-top":"6px","height":"35px", "textAlign": "right"} ),
                                                # className="me-3",
                                                width=4
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Custom CMAP",width=4),
                                                dbc.Label("min:",width=2, style = {"textAlign":"right"}),                                                
                                                dbc.Col(
                                                    dcc.Input(id='x_plane_lower_color', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("max:",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='x_plane_upper_color', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
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
                                            [
                                                dbc.Label("Y-Axis plane",style={'font-weight': 'bold'}, width = 4),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("",width=4),
                                                dbc.Label("at:",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='y_axis_plane', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("Opacity",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='y_axis_plane_color_opacity', value=pa["y_axis_plane_color_opacity"], type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                            dbc.Label("Y-CMAP",width=3, style = {"textAlign":"left"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["plane_colors"]), value=pa["y_axis_plane_color_value"] , id='y_axis_plane_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=5
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' reverse', 'value':'y_axis_reverse_color_scale'} ], value=pa["y_axis_reverse_color_scale"], id='y_axis_reverse_color_scale', style={"margin-top":"6px","height":"35px", "textAlign": "right"} ),
                                                # className="me-3",
                                                width=4
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Custom CMAP",width=4),
                                                dbc.Label("min:",width=2, style = {"textAlign":"right"}),                                                
                                                dbc.Col(
                                                    dcc.Input(id='y_plane_lower_color', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("max:",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='y_plane_upper_color', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
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
                                            [
                                                dbc.Label("Z-Axis plane",style={'font-weight': 'bold'}, width = 4),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("",width=4),
                                                dbc.Label("at:",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='z_axis_plane', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("Opacity",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='z_axis_plane_color_opacity', value=pa["z_axis_plane_color_opacity"], type='text', style=card_input_style),
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                            dbc.Label("Z-CMAP",width=3, style = {"textAlign":"left"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["plane_colors"]), value=pa["z_axis_plane_color_value"] , id='z_axis_plane_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=5
                                            ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' reverse', 'value':'z_axis_reverse_color_scale'} ], value=pa["z_axis_reverse_color_scale"], id='z_axis_reverse_color_scale', style={"margin-top":"6px","height":"35px", "textAlign": "right"} ),
                                                # className="me-3",
                                                width=4
                                            ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Custom CMAP",width=4),
                                                dbc.Label("min:",width=2, style = {"textAlign":"right"}),                                                
                                                dbc.Col(
                                                    dcc.Input(id='z_plane_lower_color', placeholder="", type='text', style=card_input_style),
                                                    width=2
                                                ),
                                                dbc.Label("max:",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='z_plane_upper_color', placeholder="", type='text', style=card_input_style),
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
                            id={'type':"collapse-dynamic-card","index":"planes"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px", "padding":"0px", "margin":"0px"} 
                ),
                html.Div(id="marker-cards"),
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
                                                dbc.Label("font size",html_for='labels_font_size',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["title_size"]), value=pa["labels_font_size"],id='labels_font_size', placeholder="size", style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Label("color",html_for='labels_font_color_value',width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["labels_font_color"]), value=pa["labels_font_color_value"], placeholder="color", id='labels_font_color_value', multi=False,clearable=False, style=card_input_style ),
                                                    width=4
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("arrows",html_for='labels_arrows_value',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["labels_arrows"]),value=pa["labels_arrows_value"], placeholder="type", id='labels_arrows_value', multi=False, style=card_input_style ),
                                                    width=3,
                                                ),
                                                dbc.Label("color",html_for='labels_colors_value',width=2,style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["labels_colors"]), value=pa["labels_colors_value"], placeholder="color", id='labels_colors_value', multi=False, clearable=False,style=card_input_style ),
                                                    width=4,
                                                )
                                            ],
                                        className="g-1",
                                        ),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("width",width=3, style = {"textAlign":"left"}),                                                
                                                dbc.Col(
                                                    dcc.Input(id='labels_line_width', value=pa["labels_line_width"], type='text', style=card_input_style),
                                                    width=3
                                                ),
                                                dbc.Label("alpha",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(id='labels_alpha', value=pa["labels_alpha"], type='text', style=card_input_style),
                                                    width=4
                                                ),
                                            ],
                                            className="g-1",
                                        ),
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
                                    dcc.Input(id='pdf-filename', value="threeDscatterplot.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="threeDscatterplot.json", type='text', style={"width":"100%"})
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
    'groups_value',
    'fig_width',
    'fig_height',
    'title',
    'titles',
    'show_legend',
    'legend_title',
    'legend_font_size',
    'xlabel',
    'xlabels',
    'ylabel',
    'ylabels',
    'zlabel',
    'zlabels',
    'show_axis',
    "show_mirror_axis",
    'axis_line_width',
    'tick_axis',
    'ticks_length',
    'ticks_direction_value',
    'xticks_fontsize',
    'xticks_rotation',
    'yticks_fontsize',
    'yticks_rotation',
    'zticks_fontsize',
    'zticks_rotation',
    'x_lower_limit',
    'x_upper_limit',
    'y_lower_limit',
    'y_upper_limit',
    'z_lower_limit',
    'z_upper_limit',
    "maxxticks",
    "maxyticks",
    "maxzticks",
    "x_axis_background_color",  
    "x_axis_background_color_text",  
    "y_axis_background_color",  
    "y_axis_background_color_text",  
    "z_axis_background_color",  
    "z_axis_background_color_text",  
    'grid_value',
    'grid_linewidth',
    'grid_color_value',
    'grid_color_text',
    "x_axis_plane",
    "x_axis_plane_color_value",
    "x_axis_reverse_color_scale",
    "x_axis_plane_color_opacity",
    "x_plane_lower_color",
    "x_plane_upper_color",
    "y_axis_plane",
    "y_axis_plane_color_value",
    "y_axis_reverse_color_scale",
    "y_axis_plane_color_opacity",
    "y_plane_lower_color",
    "y_plane_upper_color",
    "z_axis_plane",
    "z_axis_plane_color_value",
    "z_axis_reverse_color_scale",
    "z_axis_plane_color_opacity",
    "z_plane_lower_color",
    "z_plane_upper_color",
    'labels_col_value',
    'labels_font_size',
    'labels_font_color_value',
    'labels_arrows_value',
    'labels_colors_value',
    'labels_line_width',
    'labels_alpha'
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ Output('xvals', 'options'),
    Output('yvals', 'options'),
    Output('zvals', 'options'),
    Output('groups_value', 'options'),
    Output('labels_col_value', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('xvals', 'value'),
    Output('yvals', 'value'),
    Output('zvals', 'value'),
    ] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "threeDscatterplot")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            xvals=app_data['pa']["xvals"]
            yvals=app_data['pa']["yvals"]
            zvals=app_data['pa']["zvals"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"threeDscatterplot")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            xvals=cols[0]
            yvals=cols[1]
            zvals=cols[2]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )
        return [ cols_, cols_, cols_, cols_,cols_, upload_text, None, None,  xvals, yvals, zvals] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"threeDscatterplot")
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update,  dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs
   

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
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"threeDscatterplot")
            labels=df[[col]].drop_duplicates()[col].tolist()
            labels_=make_options(labels)

            if ( filename.split(".")[-1] == "json" ) and ( not update_labels_field_import ) :
                app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "threeDscatterplot")
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
        toast=make_except_toast("There was a problem updating the labels field.","update_labels_field", e, current_user,"threeDscatterplot")
        return dash.no_update, toast, tb_str, dash.no_update

@dashapp.callback( 
    Output('marker-cards', 'children'),
    Output('toast-generate_markers','children'),
    Output({ "type":"traceback", "index":"generate_markers" },'data'),
    Output('generate_markers-import', 'data'),
    Input('session-id', 'data'),
    Input('groups_value', 'value'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('generate_markers-import', 'data'),
    )
def generate_markers(session_id,groups,contents,filename,last_modified,generate_markers_import):
    pa=figure_defaults()
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_markers_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "threeDscatterplot")
            pa=app_data['pa']
            generate_markers_import=True
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"threeDscatterplot")
            cols=df.columns.tolist()
            cols_=make_options(cols)
    else:
        cols=[]
        cols_=make_options(cols)

        
    def make_card(card_header,card_id,pa,gpa, cols_):
        card=dbc.Card(
            [
                dbc.CardHeader(
                    html.H2(
                        dbc.Button( card_header, color="black", id={'type':"dynamic-card","index":str(card_id)}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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

                                        dbc.Label("Marker",width=2),
                                    ],
                                    className="g-1",
                                ),
                            ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("size",style={"textAlign":"right"},width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_size"]), value=gpa["markers"],  id={'type':"markers","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown( options=cols_, value=gpa["markersizes_col"], id={'type':"markersizes_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                            width=6
                                        )
                                    ],
                                    className="g-1",
                                ),
                            ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("shape", width=2,style={"textAlign":"right"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["markerstyles"]), value=gpa["marker"], placeholder="marker", id={'type':"marker","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown( options=cols_, value=gpa["markerstyles_col"], id={'type':"markerstyles_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                            width=6
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("color",width=2,style={"textAlign":"right"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_color"]), value=gpa["markerc"], placeholder="size", id={'type':"markerc","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                                [
                                            dcc.Dropdown( options=cols_, value=gpa["markerc_col"], id={'type':"markerc_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                                ],
                                            width=6,
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("",width=2),
                                        dbc.Col(
                                                [
                                                    dcc.Input(id={'type':"markerc_write","index":str(card_id)},value=gpa["markerc_write"], placeholder=".. or, write color name", type='text', style={"height":"35px","width":"100%"} ),
                                                ],
                                            width=10,
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("alpha",width=2,style={"textAlign":"right"}),
                                        dbc.Col(
                                            dcc.Input(id={'type':"marker_alpha","index":str(card_id)}, value=gpa["marker_alpha"],placeholder="value", type='text', style={"height":"35px","width":"100%"} ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown( options=cols_, value=gpa["markeralpha_col_value"], id={'type':"markeralpha_col_value","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                            width=6
                                        )
                                    ],
                                    className="g-1",
                                ),
                                # ############################
                                # dbc.Row([
                                #     html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                # ],
                                # className="g-1",
                                # justify="start"),
                                # ############################################
                                # dbc.Row(
                                #     [

                                #         dbc.Label("Line",width=2),
                                #     ],
                                #     className="g-1",
                                # ),
                                # ############################################
                                # dbc.Row(
                                #     [
                                #         dbc.Label("width",width=2,style={"textAlign":"right"}),
                                #         dbc.Col(
                                #             dcc.Dropdown( options=make_options(pa["edge_linewidths"]), value=gpa["edge_linewidth"], placeholder="width", id={'type':"edge_linewidth","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                #             width=4
                                #         ),
                                #         dbc.Col(
                                #             dcc.Dropdown( options=cols_, value=gpa["edge_linewidth_col"], id={'type':"edge_linewidth_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                #             width=6
                                #         )
                                #     ],
                                #     className="g-1",
                                # ),
                                # ############################################
                                # dbc.Row(
                                #     [
                                #         dbc.Label("color",width=2,style={"textAlign":"right"}),
                                #         dbc.Col(
                                #             dcc.Dropdown( options=make_options(pa["edge_colors"]), value=gpa["edgecolor"], placeholder="color", id={'type':"edgecolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                #             width=4
                                #         ),
                                #         dbc.Col(
                                #             dcc.Dropdown( options=cols_, value=gpa["edgecolor_col"], id={'type':"edgecolor_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style ),
                                #             width=6
                                #         )
                                #     ],
                                #     className="g-1",
                                # ),
                                # ############################################
                                # dbc.Row(
                                #     [
                                #         dbc.Label("",width=2),
                                #         dbc.Col(
                                #             dcc.Input(id={'type':"edgecolor_write","index":str(card_id)}, value=gpa["edgecolor_write"], placeholder=".. or, write color name", type='text', style=card_input_style ),
                                #             width=10
                                #         )
                                #     ],
                                #     className="g-1",
                                # ),
                                ############################################
                            ],
                        ),
                        style=card_body_style),
                    id={'type':"collapse-dynamic-card","index":str(card_id)},
                    is_open=False,
                ),
            ],
            style={"margin-top":"2px","margin-bottom":"2px"} 
        )

        return card

    try:

        if not groups:
            cards=[ make_card("Marker",0, pa, pa, cols_ ) ]
        else:
            cards=[]
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"threeDscatterplot")
            groups_=df[[groups]].drop_duplicates()[groups].tolist()
            for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
                if filename.split(".")[-1] == "json":
                    pa_=pa["groups_settings"][i]
                    card=make_card(g, i, pa, pa_, cols_)
                else:
                    card=make_card(g, i, pa, pa, cols_)
                cards.append(card)
        return cards, None, None, generate_markers_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"threeDscatterplot")
        return dash.no_update, toast, tb_str, dash.no_update


states=[
    State('xvals', 'value'),
    State('yvals', 'value'),
    State('zvals', 'value'),
    State('groups_value', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('title', 'value'),
    State('titles', 'value'),
    State('show_legend', 'value'),
    State('legend_title', 'value'),
    State('legend_font_size', 'value'),
    State('xlabel', 'value'),
    State('xlabels', 'value'),
    State('ylabel', 'value'),
    State('ylabels', 'value'),
    State('zlabel', 'value'),
    State('zlabels', 'value'),
    State('show_axis', 'value'),
    State('show_mirror_axis', 'value'),
    State('axis_line_width', 'value'),
    State('tick_axis', 'value'),
    State('ticks_length', 'value'),
    State('ticks_direction_value', 'value'),
    State('xticks_fontsize', 'value'),
    State('xticks_rotation', 'value'),
    State('yticks_fontsize', 'value'),
    State('yticks_rotation', 'value'),
    State('zticks_fontsize', 'value'),
    State('zticks_rotation', 'value'),
    State('x_lower_limit', 'value'),
    State('x_upper_limit', 'value'),
    State('y_lower_limit', 'value'),
    State('y_upper_limit', 'value'),
    State('z_lower_limit', 'value'),
    State('z_upper_limit', 'value'),
    State('maxxticks', 'value'),
    State('maxyticks', 'value'),
    State('maxzticks', 'value'),
    State('x_axis_background_color', 'value'),    
    State('x_axis_background_color_text', 'value'),    
    State('y_axis_background_color', 'value'),    
    State('y_axis_background_color_text', 'value'),    
    State('z_axis_background_color', 'value'),    
    State('z_axis_background_color_text', 'value'),    
    State('grid_value', 'value'),
    State('grid_linewidth', 'value'),
    State('grid_color_value', 'value'),
    State('grid_color_text', 'value'),
    State('x_axis_plane', 'value'),    
    State('x_axis_plane_color_value', 'value'),    
    State('x_axis_reverse_color_scale', 'value'),    
    State('x_axis_plane_color_opacity', 'value'),    
    State('x_plane_lower_color', 'value'),    
    State('x_plane_upper_color', 'value'),    
    State('y_axis_plane', 'value'),    
    State('y_axis_plane_color_value', 'value'),    
    State('y_axis_reverse_color_scale', 'value'),    
    State('y_axis_plane_color_opacity', 'value'),    
    State('y_plane_lower_color', 'value'),    
    State('y_plane_upper_color', 'value'),    
    State('z_axis_plane', 'value'),    
    State('z_axis_plane_color_value', 'value'),    
    State('z_axis_reverse_color_scale', 'value'),    
    State('z_axis_plane_color_opacity', 'value'),    
    State('z_plane_lower_color', 'value'),    
    State('z_plane_upper_color', 'value'),    
    State('labels_col_value', 'value'),
    State('labels_font_size', 'value'),
    State('labels_font_color_value', 'value'),
    State('labels_arrows_value', 'value'),
    State('labels_colors_value', 'value'),
    State('labels_line_width', 'value'),
    State('labels_alpha', 'value'),
    State('fixed_labels', 'value'),
    State( { 'type': 'marker', 'index': ALL }, "value"),
    State( { 'type': 'markerstyles_col', 'index': ALL }, "value"),
    State( { 'type': 'markers', 'index': ALL }, "value"),
    State( { 'type': 'markersizes_col', 'index': ALL }, "value"),
    State( { 'type': 'markerc', 'index': ALL }, "value"),
    State( { 'type': 'markerc_col', 'index': ALL }, "value"),
    State( { 'type': 'markerc_write', 'index': ALL }, "value"),
    State( { 'type': 'marker_alpha', 'index': ALL }, "value"),
    State( { 'type': 'markeralpha_col_value', 'index': ALL }, "value"),
    State( { 'type': 'edge_linewidth', 'index': ALL }, "value"),
    State( { 'type': 'edge_linewidth_col', 'index': ALL }, "value"),
    State( { 'type': 'edgecolor', 'index': ALL }, "value"),
    State( { 'type': 'edgecolor_col', 'index': ALL }, "value"),
    State( { 'type': 'edgecolor_write', 'index': ALL }, "value") 
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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"threeDscatterplot")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_

        if pa["groups_value"]:
            groups=df[[ pa["groups_value"] ]].drop_duplicates()[ pa["groups_value"] ].tolist()
            pa["list_of_groups"]=groups
            groups_settings_={}
            for i, g in enumerate(groups):
                groups_settings_[i]={"name":g}

            for k, a in zip(input_names,args):
                if type(k) == dict :
                    k_=k['type']
                    for i, a_ in enumerate(a) :
                        groups_settings_[i][k_]=a_

            groups_settings = []
            for i in list(groups_settings_.keys()):
                groups_settings.append(groups_settings_[i])

            pa["groups_settings"]=groups_settings

        session_data={ "session_data": {"app": { "threeDscatterplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION

        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"threeDscatterplot")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="threeDscatterplot.json"
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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"threeDscatterplot")
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"threeDscatterplot")
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
        pdf_filename="threeDscatterplot.pdf"
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

    eventlog = UserLogging(email=current_user.email,action="download figure threeDscatterplot")
    db.session.add(eventlog)
    db.session.commit()
    
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

        ask_for_help(tb_str,current_user, "threeDscatterplot", session_data)

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