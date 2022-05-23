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
from pyflaski.histogram import make_figure, figure_defaults
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


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("histogram",url_base_pathname=f'{PAGE_PREFIX}/histogram/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit histogram")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Histogram",current_user),
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
                ############################
                dbc.Row(
                    [
                        dbc.Label("Data Columns"),
                    ],
                    className="g-1",
                ),
                ############################
                dbc.Row(
                    [
                        dbc.Col(                        
                            dcc.Dropdown( placeholder="data columns", id='vals', multi=True, style = {"margin-bottom": "5px"}),
                        ),
                    ],
                    className="g-1",
                ),
                ############################
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
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Layout"),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' Legend', 'value':'show_legend'}, 
                                                                         {'label': ' Log scale', 'value':'log_scale'},
                                                                         {'label': ' KDE', 'value':'kde'},
                                                                         {'label': ' Error Bar', 'value':'errorbar'}], 
                                                                          value=pa["layout"], id='layout',
                                                                          labelStyle={'display': 'inline-block',"margin-right":"10px"},#,"height":"35px"},
                                                                          style={"height":"35px"},
                                                                        ),
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
                                            dbc.Label("Barmode",html_for="barmode",width=3, style={"text-align":"left"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["barmodes"]), value=pa["barmode"], id='barmode', multi=False, clearable=False, style=card_input_style),
                                                width = 9,
                                            )
                                        ],
                                        className="g-1",
                                        justify="between"
                                    ),                                
                                    ############################
                                    dbc.Row(
                                        [

                                            dbc.Label("Width",html_for="fig_width", width = 3), #"height":"35px",
                                            dbc.Col(
                                                dcc.Input(id='fig_width', placeholder="eg. 600", type='text', style=card_input_style),
                                                width = 3,
                                            ),
                                            dbc.Label("Height", html_for="fig_height", width = 3, style={"text-align":"right"}),
                                            dbc.Col(
                                                dcc.Input(id='fig_height', placeholder="eg. 600", type='text',style=card_input_style),
                                                width = 3,
                                            ),
        
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Paper color",html_for="paper_bgcolor",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["paper_bgcolor"], id='paper_bgcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 3,
                                            ),
                                            dbc.Label("Plot color",html_for="plot_bgcolor",width=3, style={"text-align":"right",}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["plot_bgcolor"], id='plot_bgcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 3,
                                            )
                                        ],
                                        className="g-1",
                                    ),       
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                    ],
                                    className="g-1",
                                    justify="start"),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Title"),
                                        ],
                                        className="g-1",
                                    ),       
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Text",width= 2,html_for="title"), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder="title", type='text', style=card_input_style) ,
                                                width = 10,
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Font",html_for="title_fontfamily",width=2),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["title_fontfamily"], id='title_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                width = 6,
                                            ),
                                            dbc.Label("size",html_for="title_fontsize",width=2, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["title_fontsize"],placeholder="size", id='title_fontsize', multi=False, clearable=False, style=card_input_style),
                                                width = 2,
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Color",html_for="title_fontcolor",width=2, style={"text-align":"left",}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["title_fontcolor"], id='title_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 10,
                                            )
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("X coordinates"),
                                        ],
                                        className="g-1",
                                    ),       
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Reference",html_for="xref",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["references"]), value=pa["xref"], id='xref', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("position",html_for="x",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["x"],id='x', type='text', style=card_input_style) ,
                                                width = 2,
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Anchor",html_for="title_xanchor",width=3, style={"text-align":"left",}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_xanchors"]), value=pa["title_xanchor"], id='title_xanchor', multi=False, clearable=False, style=card_input_style),
                                                width = 9,
                                            )
                                        ],
                                        className="g-1",
                                    ),       
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Y coordinates"),
                                        ],
                                        className="g-1",
                                    ),       
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Reference",html_for="yref",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["references"]), value=pa["yref"], id='yref', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("position",html_for="y",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["y"],id='y', type='text', style=card_input_style) ,
                                                width = 2,
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Anchor",html_for="title_yanchor",width=3, style={"text-align":"left",}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_yanchors"]), value=pa["title_yanchor"], id='title_yanchor', multi=False, clearable=False, style=card_input_style),
                                                width = 9,
                                            )
                                        ],
                                        className="g-1",
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
                                                    width=10
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("y label",html_for='ylabel',width=2),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ylabel"] ,id='ylabel', placeholder="y label", type='text', style=card_input_style) ,
                                                    width=10,
                                                ),
                                            ],
                                            className="g-1",

                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Font",html_for="label_fontfamily",width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["label_fontfamily"], id='label_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                    width = 6,
                                                ),
                                                dbc.Label("size",html_for="label_fontsize",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["label_fontsize"],placeholder="size", id='label_fontsize', multi=False, clearable=False, style=card_input_style),
                                                    width = 2,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Color",html_for="label_fontcolor",width=2, style={"text-align":"left",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["label_fontcolor"], id='label_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                    width = 10,
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
                                                            {'label': ' left   ', 'value': 'left_axis'},
                                                            {'label': ' right   ', 'value': 'right_axis'},
                                                            {'label': ' upper   ', 'value': 'upper_axis'},
                                                            {'label': ' lower   ', 'value': 'lower_axis'}
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
                                                dbc.Label("Color", width = 2), # style={"textAlign":"right","padding-right":"2px"}
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["axis_line_color"], id="axis_line_color", multi=False, clearable=False, style=card_input_style),
                                                    width=6
                                                ),
                                                dbc.Label("Width",width=2, style = {"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["axis_line_width"], id='axis_line_width', placeholder="width", type='text', style=card_input_style ) ,
                                                    width=2
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                    ],
                                    className="g-1",
                                    justify="start"),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Ticks:",html_for="tick_axis",width=2),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X   ', 'value': 'tick_x_axis'},
                                                            {'label': ' Y   ', 'value': 'tick_y_axis'},
                                                        ],
                                                        value=pa["tick_axis"],
                                                        labelStyle={'display': 'inline-block',"margin-right":"10px"},
                                                        style={"height":"35px","margin-top":"16px"},
                                                        id="tick_axis",
                                                    ),
                                                    width = 4,
                                                ),
                                                dbc.Col(
                                                    dbc.Label("direction",html_for='ticks_direction_value',style={"margin-top":"16px"}), # style={"textAlign":"right","padding-right":"2px"}
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["ticks_direction"]), value=pa["ticks_direction_value"], id="ticks_direction_value",placeholder="direction", multi=False, clearable=False, style={"margin-top":"10px"}),
                                                    width=3
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Color",html_for="ticks_color",width=2, style={"text-align":"left",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["ticks_color"], id='ticks_color', multi=False, clearable=False, style=card_input_style),
                                                    width = 10,
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
                                                    dbc.Label("width",html_for='ticks_line_width',style={"margin-top":"5px"}), # style={"textAlign":"right","padding-right":"2px"}
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ticks_line_width"], id='ticks_line_width', placeholder="width", type='text',style=card_input_style ) ,
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
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Spikes:", style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("type", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["spikes"]), placeholder="select", value = pa["spikes_value"], id='spikes_value', multi=False, style=card_input_style ),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("width", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["spikes_thickness"],id='spikes_thickness', placeholder="value", type='text', style=card_input_style ),
                                                    width=3,
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
                                                    dbc.Label("mode", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["spikes_modes"]), placeholder="select",value = pa["spikes_mode"], id='spikes_mode', multi=False, style=card_input_style ),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("dash", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["dashes"]), placeholder="select", value = pa["spikes_dash"], id='spikes_dash', multi=False, style=card_input_style ),
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
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["spikes_color"] ,placeholder="select", id='spikes_color', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=8
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                        ],
                                        className="g-1",
                                        justify="start"),
                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Grid:",style={"margin-top":"5px"}),
                                                    width=2
                                                ),
                                                dbc.Col(
                                                    dbc.Label("type", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid"]), placeholder="select", value=pa["grid_value"], id='grid_value', multi=False, style=card_input_style ),
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("width", style={"margin-top":"5px"}),
                                                    width=2,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["grid_width"],id='grid_width', placeholder="value", type='text', style=card_input_style ),
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
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["grid_color"] ,placeholder="select", id='grid_color', multi=False, clearable=False, style=card_input_style ) ,
                                                    width=8
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
                                dbc.Button( "Legend", color="black", id={'type':"dynamic-card","index":"legend"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Title"),

                                            ],
                                            className="g-1",

                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Text",html_for='legend_title',width=2),
                                                dbc.Col(
                                                    dcc.Input(value=pa["legend_title"] ,id='legend_title', placeholder="", type='text', style=card_input_style) ,
                                                    width=10,
                                                ),
                                            ],
                                            className="g-1",

                                        ),
                                        ############################ move to right side
                                        dbc.Row(
                                            [
                                                dbc.Label("", width = 5),
                                                dbc.Label("Location",html_for="legend_side",width=3, style={"text-align":"right",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["sides"]), value=pa["legend_side"], id='legend_side', multi=False, clearable=False, style=card_input_style),
                                                    width = 4,
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Font",html_for="legend_title_fontfamily",width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["legend_title_fontfamily"], id='legend_title_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                    width = 6,
                                                ),
                                                dbc.Label("size",html_for="legend_title_fontsize",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["legend_title_fontsize"],placeholder="size", id='legend_title_fontsize', multi=False, clearable=False, style=card_input_style),
                                                    width = 2,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Color",html_for="legend_title_fontcolor",width=2, style={"text-align":"left",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_title_fontcolor"], id='legend_title_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                    width = 10,
                                                )
                                            ],
                                            className="g-1",
                                        ),       
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("X coordinates"),
                                            ],
                                            className="g-1",
                                        ),       
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Position",html_for="legend_x",width=3, style={"textAlign":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["legend_x"],id='legend_x', type='text', style=card_input_style) ,
                                                    width = 2,
                                                ),
                                                dbc.Label("Anchor",html_for="legend_xanchor",width=3, style={"text-align":"right",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_xanchors"]), value=pa["legend_xanchor"], id='legend_xanchor', multi=False, clearable=False, style=card_input_style),
                                                    width = 4,
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Y coordinates"),
                                            ],
                                            className="g-1",
                                        ),       
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Position",html_for="legend_y",width=3, style={"textAlign":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["legend_y"],id='legend_y', type='text', style=card_input_style) ,
                                                    width = 2,
                                                ),
                                                dbc.Label("Anchor",html_for="legend_yanchor",width=3, style={"text-align":"right",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_yanchors"]), value=pa["legend_yanchor"], id='legend_yanchor', multi=False, clearable=False, style=card_input_style),
                                                    width = 4,
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row([
                                            html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                        ],
                                        className="g-1",
                                        justify="start"),

                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Main Body"),

                                            ],
                                            className="g-1",

                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Font",html_for="legend_fontfamily",width=2),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["legend_fontfamily"], id='legend_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                    width = 6,
                                                ),
                                                dbc.Label("size",html_for="legend_fontsize",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["legend_fontsize"],placeholder="size", id='legend_fontsize', multi=False, clearable=False, style=card_input_style),
                                                    width = 2,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Color",html_for="legend_fontcolor",width=2, style={"text-align":"left",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_fontcolor"], id='legend_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                    width = 10,
                                                )
                                            ],
                                            className="g-1",
                                        ),       
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("BKG",html_for="legend_bgcolor",width=2, style={"text-align":"left",}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_bgcolor"], id='legend_bgcolor', multi=False, clearable=False, style=card_input_style),
                                                    width = 10,
                                                )
                                            ],
                                            className="g-1",
                                        ),       
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Orientation",html_for="legend_orientation",width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["orientations"]), value=pa["legend_orientation"], id='legend_orientation', multi=False, clearable=False, style=card_input_style),
                                                    width = 3,
                                                ),
                                                dbc.Label("Alignment",html_for="legend_valign",width=3, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["valignments"]), value=pa["legend_valign"], id='legend_valign', multi=False, clearable=False, style=card_input_style),
                                                    width = 3,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Border",width=2),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("color",html_for="legend_bordercolor",width=2, style = {"textAlign": "right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_bordercolor"], id='legend_bordercolor', multi=False, clearable=False, style=card_input_style),
                                                    width = 6,
                                                ),
                                                dbc.Label("width",html_for="legend_borderwidth",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["legend_borderwidth"],id='legend_borderwidth', type='text', style=card_input_style) ,
                                                    width = 2,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("Trace",width=2),
                                            ],
                                            className="g-1",
                                        ),
                                        ############################
                                        dbc.Row(
                                            [
                                                dbc.Label("order",html_for="legend_traceorder",width=2, style = {"textAlign": "right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["traceorders"]), value=pa["legend_traceorder"], id='legend_traceorder', multi=False, clearable=False, style=card_input_style),
                                                    width = 6,
                                                ),
                                                dbc.Label("gap",html_for="legend_tracegroupgap",width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["legend_tracegroupgap"],id='legend_tracegroupgap', type='text', style=card_input_style) ,
                                                    width = 2,
                                                ),
                                            ],
                                            className="g-1",
                                        ),
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"legend"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                html.Div(id="extra-cards"),
                html.Div(id="marker-cards"),
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
            # dcc.Store( id='update_labels_field-import'),
            dcc.Store( id='generate_extras-import'),
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
                                    # html.Div( id="toast-update_labels_field"  ),
                                    # dcc.Store( id={ "type":"traceback", "index":"update_labels_field" }), 
                                    html.Div( id="toast-generate_extras" ),
                                    dcc.Store( id={ "type":"traceback", "index":"generate_extras" }), 
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
                                    dcc.Input(id='pdf-filename', value="histogram.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="histogram.json", type='text', style={"width":"100%"})
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
    'layout',
    'barmode',
    'fig_width',
    'fig_height',
    'paper_bgcolor',
    'plot_bgcolor',
    'title',
    'title_fontfamily',
    'title_fontsize',
    'title_fontcolor',
    'xref',
    'x',
    'title_xanchor',
    'yref',
    'y',
    'title_yanchor',
    'xlabel',
    'ylabel',
    'label_fontfamily',
    'label_fontsize',
    'label_fontcolor',
    'show_axis',
    'axis_line_color',
    'axis_line_width',
    'tick_axis',
    'ticks_direction_value',
    'ticks_color',
    'ticks_length',
    'ticks_line_width',
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
    'spikes_value',
    'spikes_mode',
    'spikes_dash',
    'spikes_color',
    'grid_value',
    'grid_width',
    'grid_color',
    'legend_title',
    'legend_side',
    'legend_title_fontfamily',
    'legend_title_fontsize',
    'legend_title_fontcolor',
    'legend_x',
    'legend_xanchor',
    'legend_y',
    'legend_yanchor',
    'legend_fontfamily',
    'legend_fontsize',
    'legend_fontcolor',
    'legend_bgcolor',
    'legend_orientation',
    'legend_valign',
    'legend_bordercolor',
    'legend_borderwidth',
    'legend_traceorder',
    'legend_tracegroupgap',
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [Output('vals', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('vals', 'value')] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "histogram")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            vals=app_data['pa']["vals"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"histogram")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            vals=cols

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [ cols_, upload_text, None, None,  vals,] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"histogram")
        return [ dash.no_update, dash.no_update,  toast, tb_str, dash.no_update] + pa_outputs


@dashapp.callback( 
    Output('extra-cards', 'children'),
    Output('toast-generate_extras','children'),
    Output({ "type":"traceback", "index":"generate_extras" },'data'),
    Output('generate_extras-import', 'data'),
    Input('session-id', 'data'),
    Input('vals', 'value'),
    Input('layout', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('generate_extras-import', 'data'),
    )
def generate_extras(session_id,groups, layout,contents,filename,last_modified,generate_extras_import):
    pa=figure_defaults()
    print("extra cards")
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_extras_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "histogram")
            pa=app_data['pa']
            generate_extras_import=True

        
    def make_card(card_header,pa, selected_style):
        if card_header == "Errorbar":
            if "errorbar" in selected_style:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"inline-block"}
                card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 
            else:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"none"}
                card_style_on_off={"margin-top":"0px","margin-bottom":"0px", 'display':"none" } 
                # card_style_on_off="none"

            card=dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(
                            dbc.Button( "Error bars", color="black", id={'type':"dynamic-card","index":"errorbar"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                            dbc.Label("Type",html_for="errorbar_type",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["errorbar_types"]), value=pa["errorbar_type"], id='errorbar_type', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("Width",html_for="errorbar_width",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["errorbar_width"], id='errorbar_width', multi=False, clearable=False, style=card_input_style),
                                                width = 2,
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("Color",html_for="errorbar_color",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["errorbar_color"], id='errorbar_color', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("Thickness",html_for="errorbar_thickness",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["errorbar_thickness"], id='errorbar_thickness', multi=False, clearable=False, style=card_input_style),
                                                width = 2,
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("", width = 3),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' Symmetric', 'value':'errorbar_symmetric'}], 
                                                                          value=pa["errorbar_symmetric"], id='errorbar_symmetric',
                                                                          labelStyle={'display': 'inline-block',"margin-right":"10px"},#,"height":"35px"},
                                                                          style={"height":"35px"},
                                                                        ),
                                                # className="me-3",
                                                width=4
                                            ),
                                            dbc.Label("Value",html_for="errorbar_value",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["errorbar_value"],id='errorbar_value', type='text', style=card_input_style) ,
                                                width = 2,
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                ],
                            ),
                            style=card_body_style),
                        id={'type':"collapse-dynamic-card","index":'errorbar'},
                        is_open=False,
                    ),
                ],
                style=card_style_on_off
            )
        if card_header == "KDE":
            if "kde" in selected_style:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"inline-block"}
                card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 
            else:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"none"}
                card_style_on_off={"margin-top":"0px","margin-bottom":"0px", 'display':"none" } 
                # card_style_on_off="none"

            card=dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(
                            dbc.Button( "Kernal Density Estimator (KDE)", color="black", id={'type':"dynamic-card","index":"kde"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'label':' Histogram', 'value':'show_hist'}, 
                                                                         {'label': ' Rug', 'value':'show_rug'},
                                                                         {'label': ' Curve', 'value':'show_curve'}], 
                                                                          value=pa["kde_type"], id='kde_type',
                                                                          labelStyle={'display': 'inline-block',"margin-right":"10px"},#,"height":"35px"},
                                                                          style={"height":"35px", "textAlign": "center"},
                                                                        ),
                                                # className="me-3",
                                                # width=5
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("Curve type",html_for="curve_type",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["curve_types"]), value=pa["curve_type"], id='curve_type', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("Bin size",html_for="bin_size",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["bin_size"],id='bin_size', type='text', style=card_input_style) ,
                                                width = 2,
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("Normalization",html_for="kde_histnorm",width=3),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["kde_histnorms"]), value=pa["kde_histnorm"], id='kde_histnorm', multi=False, clearable=False, style=card_input_style),
                                                width = 4,
                                            ),
                                            dbc.Label("Rug text",html_for="rug_text",width=3, style={"textAlign":"right"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["rug_text"],id='rug_text', type='text', style=card_input_style) ,
                                                width = 2,
                                            ),
                                        ],
                                        # justify="start",
                                        className="g-1",
                                    ),
                                    ############################################
                                ],
                            ),
                            style=card_body_style),
                        id={'type':"collapse-dynamic-card","index":'kde'},
                        is_open=False,
                    ),
                ],
                style=card_style_on_off
            )
        return card
    
    try:
        cards=[]
        for extra in ["Errorbar", "KDE"]:
            if extra == "Errorbar":
                # cards=[ make_card("Marker",0, pa, pa) ]
                card=make_card("Errorbar", pa, layout)
                cards.append(card)
            if extra == 'KDE':
                # include color options for different groups
                card=make_card("KDE", pa, layout)
                cards.append(card)
        return cards, None, None, generate_extras_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_extras", e, current_user,"histogram")
        return dash.no_update, toast, tb_str, dash.no_update



@dashapp.callback( 
    Output('marker-cards', 'children'),
    Output('toast-generate_markers','children'),
    Output({ "type":"traceback", "index":"generate_markers" },'data'),
    Output('generate_markers-import', 'data'),
    Input('session-id', 'data'),
    Input('vals', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('generate_markers-import', 'data'),
    )
def generate_markers(session_id,groups, contents,filename,last_modified,generate_markers_import):
    pa=figure_defaults()
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_markers_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "histogram")
            pa=app_data['pa']
            generate_markers_import=True

        
    def make_card(card_header,card_id,pa,gpa):

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
                                        dbc.Label("Main Body"),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Label",width=3),
                                        dbc.Col(
                                            dbc.Input(value=gpa["hist_label"], id={'type':"hist_label","index":str(card_id)}, placeholder="", type="text", style=card_input_style ),
                                            width=9
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Direction",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["cumulative_directions"]), value=gpa["cumulative_direction"],  id={'type':"cumulative_direction","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Label("",width=1),
                                        dbc.Col(
                                            dcc.Checklist(
                                                options=[
                                                    {'label': ' Cumulative', 'value': 'cumulative'},], value=gpa['cumulative'], id={'type':"cumulative","index":str(card_id)}, style={"margin-top":"6px"}, 
                                            ),
                                            width=4,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Function",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["histfuncs"]), value=gpa["histfunc"],  id={'type':"histfunc","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Label("alpha",width=2, style = {"textAlign": "right"}),
                                        dbc.Col(
                                            dbc.Input(value=gpa["opacity"], id={'type':"opacity","index":str(card_id)}, placeholder="", type="text", style=card_input_style ),
                                            width=3,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Color",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=gpa["color_value"],  id={'type':"color_value","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["color_rgb"], id={'type':"color_rgb","index":str(card_id)}, placeholder=".. or write", type="text", style=card_input_style ),
                                            width=5,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Border color",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=gpa["line_color"],  id={'type':"line_color","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["line_rgb"], id={'type':"line_rgb","index":str(card_id)}, placeholder=".. or write", type="text", style=card_input_style ),
                                            width=5,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Border style",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["linestyles"]), value=gpa["linestyle_value"],  id={'type':"linestyle_value","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Label("width",width=2, style = {"textAlign": "right"}),
                                        dbc.Col(
                                            dbc.Input(value=gpa["linewidth"], id={'type':"linewidth","index":str(card_id)}, placeholder="", type="text", style=card_input_style ),
                                            width=3,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Histnorm",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["histnorms"]), value=gpa["histnorm"],  id={'type':"histnorm","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Label("N bins",width=2, style = {"textAlign": "right"}),
                                        dbc.Col(
                                            dbc.Input(value=gpa["bins_number"], id={'type':"bins_number","index":str(card_id)}, placeholder="", type="text", style=card_input_style ),
                                            width=3,
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Orientation",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["orientations"]), value=gpa["orientation_value"],  id={'type':"orientation_value","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px"})
                                ],
                                className="g-1",
                                justify="start"),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Hover",width=2),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Text",width=3),
                                        dbc.Col(
                                            dbc.Input(value=gpa["text"], id={'type':"text","index":str(card_id)}, placeholder="", type="text", style=card_input_style ),
                                            width=9
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Display",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hoverinfos"]), value=gpa["hoverinfo"],  id={'type':"hoverinfo","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=3
                                        ),
                                        dbc.Label("Alignment",width=3, style = {"textAlign": "right"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hover_alignments"]), value=gpa["hover_align"],  id={'type':"hover_align","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=3
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Color",width=2),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Border",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=gpa["hover_bordercolor"],  id={'type':"hover_bordercolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=3
                                        ),
                                        dbc.Label("BKG",width=3, style = {"textAlign": "right"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=gpa["hover_bgcolor"],  id={'type':"hover_bgcolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=3
                                        ),
                                    ],
                                    # justify="start",
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Font",width=3),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fonts"]), value=gpa["hover_fontfamily"],  id={'type':"hover_fontfamily","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width = 5,
                                        ),
                                        dbc.Label("size",width=2, style={"textAlign":"right"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fontsizes"]), value=gpa["hover_fontsize"],  id={'type':"hover_fontsize","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width = 2,
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("Color",width=3, style={"text-align":"left",}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=gpa["hover_fontcolor"],  id={'type':"hover_fontcolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width = 9,
                                        )
                                    ],
                                    className="g-1",
                                ),       
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
            # cards=[ make_card("Marker",0, pa, pa) ]
            cards = None
        if groups:
            cards=[]
            for g, i in zip(  groups, list( range( len(groups) ) )  ):
                if filename.split(".")[-1] == "json" and not filename in ["<from MDS app>.json", "<from PCA app>.json", "<from tSNE app>.json"]:
                    pa_=pa["groups_settings"][i]
                    card_header = "%s" %(g)
                    card=make_card(card_header, i, pa, pa_)
                else:
                    card_header = "%s" %(g)
                    card=make_card(card_header, i, pa, pa)
                cards.append(card)
        return cards, None, None, generate_markers_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"histogram")
        return dash.no_update, toast, tb_str, dash.no_update


states=[
    State('vals', 'value'),
    State('layout', 'value'),
    State('barmode', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('paper_bgcolor', 'value'),
    State('plot_bgcolor', 'value'),
    State('title', 'value'),
    State('title_fontfamily', 'value'),
    State('title_fontsize', 'value'),
    State('title_fontcolor', 'value'),
    State('xref', 'value'),
    State('x', 'value'),
    State('title_xanchor', 'value'),
    State('yref', 'value'),
    State('y', 'value'),
    State('title_yanchor', 'value'),
    State('xlabel', 'value'),
    State('ylabel', 'value'),
    State('label_fontfamily', 'value'),
    State('label_fontsize', 'value'),
    State('label_fontcolor', 'value'),
    State('show_axis', 'value'),
    State('axis_line_color', 'value'),
    State('axis_line_width', 'value'),
    State('tick_axis', 'value'),
    State('ticks_direction_value', 'value'),
    State('ticks_color', 'value'),
    State('ticks_length', 'value'),
    State('ticks_line_width', 'value'),
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
    State('spikes_value', 'value'),
    State('spikes_mode', 'value'),
    State('spikes_dash', 'value'),
    State('spikes_color', 'value'),
    State('grid_value', 'value'),
    State('grid_width', 'value'),
    State('grid_color', 'value'),
    State('legend_title', 'value'),
    State('legend_side', 'value'),
    State('legend_title_fontfamily', 'value'),
    State('legend_title_fontsize', 'value'),
    State('legend_title_fontcolor', 'value'),
    State('legend_x', 'value'),
    State('legend_xanchor', 'value'),
    State('legend_y', 'value'),
    State('legend_yanchor', 'value'),
    State('legend_fontfamily', 'value'),
    State('legend_fontsize', 'value'),
    State('legend_fontcolor', 'value'),
    State('legend_bgcolor', 'value'),
    State('legend_orientation', 'value'),
    State('legend_valign', 'value'),
    State('legend_bordercolor', 'value'),
    State('legend_borderwidth', 'value'),
    State('legend_traceorder', 'value'),
    State('legend_tracegroupgap', 'value'),
    State('kde_type', 'value'),
    State('curve_type', 'value'),
    State('bin_size', 'value'),
    State('kde_histnorm', 'value'),
    State('rug_text', 'value'),
    State('errorbar_type', 'value'),
    State('errorbar_width', 'value'),
    State('errorbar_color', 'value'),
    State('errorbar_thickness', 'value'),
    State('errorbar_symmetric', 'value'),
    State('errorbar_value', 'value'),    
    State( { 'type': 'hist_label', 'index': ALL }, "value"),
    State( { 'type': 'cumulative_direction', 'index': ALL }, "value"),
    State( { 'type': 'cumulative', 'index': ALL }, "value"),
    State( { 'type': 'histfunc', 'index': ALL }, "value"),
    State( { 'type': 'opacity', 'index': ALL }, "value"),
    State( { 'type': 'color_value', 'index': ALL }, "value"),
    State( { 'type': 'color_rgb', 'index': ALL }, "value"),
    State( { 'type': 'line_color', 'index': ALL }, "value"),
    State( { 'type': 'line_rgb', 'index': ALL }, "value"),
    State( { 'type': 'linestyle_value', 'index': ALL }, "value"),
    State( { 'type': 'linewidth', 'index': ALL }, "value"),
    State( { 'type': 'histnorm', 'index': ALL }, "value"),
    State( { 'type': 'bins_number', 'index': ALL }, "value"),
    State( { 'type': 'orientation_value', 'index': ALL }, "value"),
    State( { 'type': 'text', 'index': ALL }, "value"),
    State( { 'type': 'hoverinfo', 'index': ALL }, "value"),
    State( { 'type': 'hover_align', 'index': ALL }, "value"),
    State( { 'type': 'hover_bordercolor', 'index': ALL }, "value"),
    State( { 'type': 'hover_bgcolor', 'index': ALL }, "value"),
    State( { 'type': 'hover_fontfamily', 'index': ALL }, "value"),
    State( { 'type': 'hover_fontsize', 'index': ALL }, "value"),
    State( { 'type': 'hover_fontcolor', 'index': ALL }, "value"),
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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"histogram")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_

        if pa["vals"]:
            groups=pa["vals"]
            pa["list_of_groups"]=groups
            groups_settings_={}
            for i, g in enumerate(groups):
                groups_settings_[g]={'name': g}

            for k, a in zip(input_names,args):
                if type(k) == dict :
                    k_=k['type']
                    for i, a_ in enumerate(a) :
                        groups_settings_[groups[i]][k_]=a_

            # print(groups_settings_)
            # groups_settings = []
            # for i in list(groups_settings_.keys()):
            #     groups_settings.append(groups_settings_[i])

            pa["groups_settings"]=groups_settings_

        session_data={ "session_data": {"app": { "histogram": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"histogram")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="histogram.json"
        export_filename=secure_filename(export_filename)
        if export_filename.split(".")[-1] != "json":
            export_filename=f'{export_filename}.json'  

        def write_json(export_filename,session_data=session_data):
            export_filename.write(json.dumps(session_data).encode())
            # export_filename.seek(0)

        return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "save-session-btn" :
        try:
            if filename.split(".")[-1] == "json" and not filename in ["<from MDS app>.json", "<from DAVID app>.json", "<from PCA app>.json", "<from tSNE app>.json"]:
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None, dash.no_update, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"histogram")
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"histogram")
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
        pdf_filename="histogram.pdf"
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

    eventlog = UserLogging(email=current_user.email,action="download figure histogram")
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

        ask_for_help(tb_str,current_user, "histogram", session_data)

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