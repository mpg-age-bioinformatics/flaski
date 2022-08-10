from urllib import response
from plotly import optional_imports
from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from myapp.models import UserLogging
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, make_table
from pyflaski.lifespan import make_figure, figure_defaults
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

import plotly.tools as tls   

#print(help(tls.mpl_to_plotly))
PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("lifespan",url_base_pathname=f'{PAGE_PREFIX}/lifespan/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit lifespan")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Lifespan",current_user),
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
                                [
                                    dbc.Label("Time", style={"margin-bottom":"2px"}),
                                    dcc.Dropdown( placeholder="Time column", id='xvals', multi=False)
                                ],
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
                                    dbc.Label("Death", style={"margin-bottom":"2px", "margin-top":"10px"}),
                                    dcc.Dropdown( placeholder="Death column", id='yvals', multi=False)
                                ],
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
                                    dbc.Label("Censors" , style={"margin-bottom":"2px", "margin-top":"10px"}),
                                    dcc.Dropdown(placeholder="Censors column", id='censors_val', multi=False)
                                ],
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
                                    dbc.Label("Groups", style={"margin-bottom":"2px", "margin-top":"10px"} ),
                                    dcc.Dropdown(placeholder="Groups column", id='groups_value', multi=False)
                                ],
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
                ),
                html.Div(id="labels-section"),
                 
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
                                    dbc.Row(
                                        [

                                            dbc.Label("Width:",html_for="fig_width", style={"margin-top":"10px","width":"64px",}), #"height":"35px",
                                            dbc.Col(
                                                dcc.Input( id='fig_width', placeholder="eg. 600", type='text' , style={"height":"35px","width":"100%", "margin-top":"5px"}),
                                                style={"margin-right":"5px"}
                                            ),
                                            dbc.Label("Height:", html_for="fig_height",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"left"}),
                                            dbc.Col(
                                                dcc.Input(id='fig_height', placeholder="eg. 600", type='text',style={"height":"35px","width":"100%", "margin-top":"5px"}) ,
                                            ),
        
                                        ],
                                        className="g-1",
                                        align="center",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Title:",html_for="title",style={"margin-top":"10px","width":"64px"}), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder=pa["title"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                style={"margin-right":"5px"},
                                            ),
                                            dbc.Label("Size:",html_for="titles", style={"text-align":"left","margin-left":"5px","margin-top":"10px","width":"64px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["titles"], placeholder="size", 
                                                id='titles', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                            )
                                        ],
                                        className="g-1",
                                        align="center",
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
                    style={"margin-top":"4px","margin-bottom":"2px"} 
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
                                        dbc.Row(
                                            [
                                                dbc.Label("X label:",html_for='xlabel',style={"width":"60px","margin-top":"10px","text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xlabel"],id='xlabel', placeholder=pa["xlabel"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                
                                                dbc.Label("Size:",html_for='xlabels',style={"width":"40px","margin-top":"10px","text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["xlabel_size"]), value=pa["xlabels"], placeholder=pa["xlabels"], 
                                                    id='xlabels', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                    #style={"margin-right":"5px"} 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                            #justify="between",
                                        ),
                                        #################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Y label:",html_for='ylabel',style={"width":"60px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ylabel"],id='ylabel', placeholder=pa["ylabel"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Size:",html_for='ylabels',style={"width":"40px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["ylabel_size"]), value=pa["ylabels"], placeholder=pa["ylabels"], 
                                                    id='ylabels', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Axis:",html_for="show_axis", style={"width":"60px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' left   ',  'value': 'left_axis'},
                                                            {'label': ' right   ', 'value': 'right_axis'},
                                                            {'label': ' upper   ', 'value': 'upper_axis'},
                                                            {'label': ' lower   ', 'value': 'lower_axis'}
                                                            
                                                        ],
                                                        value=pa["show_axis"],
                                                        labelStyle={'display': 'inline-block', "margin-right":"10px"},#,"height":"35px"}, "margin-right":"110px",
                                                        style={"height":"35px","margin-top":"16px", "width":"100%" },
                                                        #inputStyle={"margin-right": "20px"},
                                                        id="show_axis"
                                                    ),
                                                )

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Border width:",html_for='axis_line_width',style={"width":"110px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["axis_line_width"],id='axis_line_width', placeholder=pa["axis_line_width"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
 
                                                ),
                                                
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Ticks:",html_for="show_axis", style={"width":"60px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X Axis   ',  'value': 'tick_x_axis'}, #"tick_x_axis","tick_y_axis"
                                                            {'label': ' Y Axis   ', 'value': 'tick_y_axis'},
                                                            #{'label': ' upper   ', 'value': 'tick_upper_axis'},
                                                           # {'label': ' lower   ', 'value': 'tick_lower_axis'}
                                                            
                                                        ],
                                                        value=["tick_x_axis", "tick_y_axis"],
                                                        labelStyle={'display': 'inline-block', "margin-right":"60px"},#,"height":"35px"}, "margin-right":"110px",
                                                        style={"height":"35px","margin-top":"10px", "width":"100%" },
                                                        #inputStyle={"margin-right": "20px"},
                                                        id="show_ticks"
                                                    ),
                                                )

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick length:",html_for='ticks_length',style={"width":"100px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["ticks_length"],id='ticks_length', placeholder=pa["ticks_length"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Tick direction:",html_for='ylabels',style={"width":"110px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["ticks_direction"]), value=pa["ticks_direction_value"], placeholder=pa["ticks_direction_value"], 
                                                    id='ticks_direction_value', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("X ticks" ,style={"width":"100px","margin-top":"10px"}),
                                                dbc.Label("Fontsize:",html_for='xticks_fontsize',style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xticks_fontsize"],id='xticks_fontsize', placeholder=pa["xticks_fontsize"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Rotation:",html_for='xticks_rotation',style={"width":"80px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xticks_rotation"],id='xticks_rotation', placeholder=pa["xticks_rotation"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Y ticks" ,style={"width":"100px","margin-top":"10px"}),
                                                dbc.Label("Fontsize:",html_for='yticks_fontsize',style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yticks_fontsize"],id='yticks_fontsize', placeholder=pa["yticks_fontsize"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Rotation:",html_for='yticks_rotation',style={"width":"80px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yticks_rotation"],id='yticks_rotation', placeholder=pa["yticks_rotation"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("X limits" ,style={"width":"100px","margin-top":"10px"}),
                                                dbc.Label("Lower:",html_for='x_lower_limit',style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["x_lower_limit"],id='x_lower_limit', placeholder=pa["x_lower_limit"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Upper:",html_for='x_upper_limit',style={"width":"80px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["x_upper_limit"],id='x_upper_limit', placeholder=pa["x_upper_limit"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Y limits" ,style={"width":"100px","margin-top":"10px"}),
                                                dbc.Label("Lower:",html_for='y_lower_limit',style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["y_lower_limit"],id='y_lower_limit', placeholder=pa["y_lower_limit"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Upper:",html_for='y_upper_limit',style={"width":"80px","margin-top":"10px", "text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["y_upper_limit"],id='y_upper_limit', placeholder=pa["y_upper_limit"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Grid:" ,style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid"]), value=pa["grid_value"], placeholder=pa["grid_value"], 
                                                    id='grid_value', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                ),

                                                dbc.Label("Width:",html_for='grid_linewidth',style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["grid_linewidth"],id='grid_linewidth', placeholder=pa["grid_linewidth"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    
                                                ),
                                                
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Grid style:" ,style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid_linestyle"]), value=pa["grid_linestyle_value"], placeholder=pa["grid_linestyle_value"], 
                                                    id='grid_linestyle_value', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                ),
                                                
                                                dbc.Label("Grid color:" ,style={"width":"80px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["grid_colors"]), value=pa["grid_color_value"], placeholder=pa["grid_color_value"], 
                                                    id='grid_color_value', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("... or write a color name",html_for='grid_color_text',style={"width":"180px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["grid_color_text"],id='grid_color_text', placeholder=pa["grid_color_text"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    
                                                ),
                                                
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #####################################
                                     
                                        ######## END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"axes"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                html.Div(id="marker-cards"),
                
             ],
            body=True,
            style={"min-width":"372px","width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"0px"}#,'display': 'block'}#,"max-width":"375px","min-width":"375px"}"display":"inline-block"
        ),
       # html.Div(id="marker-cards"),

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
            dcc.Store( id='generate_markers-import' ),
            
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
                                    ),

                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results (xlsx)" 
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
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results (xlsx)" 
                                                    ]
                                                ),
                                                id='save-excel-btn3', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='save-excel')
                                        ],
                                        id="save-excel-div3",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),

                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results (xlsx)" 
                                                    ]
                                                ),
                                                id='save-excel-btn4', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='save-excel')
                                        ],
                                        id="save-excel-div4",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),             

                                ],
                                style={"height":"100%"}
                            ),
                            html.Div(
                                [
                                    html.Div( id="toast-read_input_file"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"read_input_file" }), 
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
                                    dcc.Input(id='excel-filename', value="lifespan.xlsx", type='text', style={"width":"100%"})
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
                            dbc.ModalHeader("File name"), # dbc.ModalTitle(
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='pdf-filename', value="lifespan.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="lifespan.json", type='text', style={"width":"100%"})
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
        "fig_width",
        "fig_height",
        "title",
        "titles",
        "groups_value",
        "censors_val",
        "xlabel",
        "xlabels",
        "ylabel",
        "ylabels",
        "show_axis",
        "axis_line_width",
        "show_ticks",
        "ticks_length",
        "ticks_direction_value",
        "xticks_fontsize",
        "yticks_fontsize",
        "xticks_rotation",
        "yticks_rotation",
        "x_lower_limit",
        "y_lower_limit",
        "x_upper_limit",
        "y_upper_limit",
        "grid_value",
        "grid_linewidth",
        "grid_color_value",
        #"grid_linestyle_value" 
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ Output('xvals', 'options'),
    Output('yvals', 'options'),
    Output('censors_val', 'options'),
    Output('groups_value', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Output('xvals', 'value'),
    Output('yvals', 'value'),  ] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "lifespan")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            xvals=app_data['pa']["xvals"]
            yvals=app_data['pa']["yvals"]
            #censors_val=app_data['pa']["censors_val"]
            
            pa=app_data["pa"]
            
            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            xvals=cols[0]
            yvals=cols[1]
            #censors_val=cols[2]
            
            
        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )

        return [ cols_, cols_, cols_, cols_, upload_text, None, None,  xvals, yvals] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        print(tb_str)
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"lifespan")
        print(toast)
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs






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
def generate_markers(session_id,groups, contents,filename,last_modified,generate_markers_import):
    pa=figure_defaults()
    
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_markers_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "lifespan")
            pa=app_data['pa']
            print(pa["groups_settings"])
            generate_markers_import=True

    #         df=pd.read_json(app_data["df"])
    #         cols=df.columns.tolist()
    #         cols_=make_options(cols)
    #     else:
    #         df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
    #         cols=df.columns.tolist()
    #         cols_=make_options(cols)
    # else:
    #     cols=[]
    #     cols_=make_options(cols)

        
    def make_card(card_header,card_id,pa,gpa): #cols_, field_style_on_off
        #card_input_style={"height":"35px","width":"100%"}
        #card_input_style_dynamic={"height":"35px","width":"100%", 'display':field_style_on_off}
        
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

                                        dbc.Label("Main Line settings:", style={'font-weight': 'bold'}),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Width:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["linewidth_write"], placeholder=gpa["linewidth_write"], type='text', id={'type':"linewidth_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            style={"margin-right":"5px"},
                                        ),

                                        dbc.Label("Style:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["linestyles"]), value=gpa["linestyle_value"], placeholder=gpa["linestyle_value"], 
                                            id={'type':"linestyle_value","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Color:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["line_colors"]), value=gpa["line_color_value"], placeholder=gpa["line_color_value"], 
                                            id={'type':"line_color_value","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("... or write a color name", style={"margin-top":"10px", "width":"180px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["linecolor_write"], placeholder=gpa["linecolor_write"], type='text', id={'type':"linecolor_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            #style={"margin-right":"5px"},
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [

                                        dbc.Label("Plot Settings:", style={'font-weight': 'bold', "margin-top":"10px"}),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dcc.Checklist(
                                                options=[
                                                    {'label': ' Plot Confidence Interval lines   ', 'value': 'ci_force_lines'},
                                                    {'label': ' Shade Confidence Intervals   ',  'value': 'Conf_Interval'},
                                                    {'label': ' Plot Censors   ', 'value': 'show_censors'},
                                                    {'label': ' Legend   ', 'value': 'ci_legend'}                       
                                                    
                                                ],
                                                value=gpa["model_settings"],
                                                labelStyle={'display': 'inline-block', "margin-right":"20px"},#,"height":"35px"}, "margin-right":"110px",
                                                style={"height":"35px", "width":"100%" , "margin-bottom":"30px"}, #"margin-top":"2px
                                                #inputStyle={"margin-right": "20px"},
                                                id={'type':"model_settings","index":str(card_id)}
                                            ),
                                        )
                                    ],
                                    className="g-1",
                                    align="center",
                                ),


                                ############################################
                                dbc.Row(
                                    [

                                        dbc.Label("Confidence Intervals:", style={'font-weight': 'bold', "margin-top":"20px"}),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                
                                dbc.Row(
                                    [
                                        dbc.Label("CI Line Width:", style={"margin-top":"10px", "width":"120px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["ci_linewidth_write"], placeholder=gpa["ci_linewidth_write"], type='text', id={'type':"ci_linewidth_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            style={"margin-right":"5px"},
                                        ),

                                        dbc.Label("Style:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["linestyles"]), value=gpa["ci_linestyle_value"], placeholder=gpa["ci_linestyle_value"], 
                                            id={'type':"ci_linestyle_value","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Color:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["line_colors"]), value=gpa["ci_line_color_value"], placeholder=gpa["ci_line_color_value"], 
                                            id={'type':"ci_line_color_value","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("... or write a color name", style={"margin-top":"10px", "width":"180px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["ci_linecolor_write"], placeholder=gpa["ci_linecolor_write"], type='text', id={'type':"ci_linecolor_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("CI Aplha:", style={"margin-top":"10px", "width":"80px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["ci_alpha"], placeholder=gpa["ci_alpha"], type='text', id={'type':"ci_alpha","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),

                                ############################################
                                dbc.Row(
                                    [

                                        dbc.Label("Censor marker settings:", style={'font-weight': 'bold', "margin-top":"20px" }),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Shape:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["censor_marker"]), value=gpa["censor_marker_value"], placeholder=gpa["censor_marker_value"], 
                                            id={'type':"censor_marker_value","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            style={"margin-right":"5px"},
                                        ),

                                        dbc.Label("Size:", style={"margin-top":"10px", "width":"60px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["censor_marker_size"]), value=gpa["censor_marker_size_val"], placeholder=gpa["censor_marker_size_val"], 
                                            id={'type':"censor_marker_size_val","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Edge width:", style={"margin-top":"10px", "width":"100px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["edge_linewidths"]), value=gpa["edge_linewidth"], placeholder=gpa["edge_linewidth"], 
                                            id={'type':"edge_linewidth","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            style={"margin-right":"5px"},
                                        ),

                                        dbc.Label("Face color:", style={"margin-top":"10px", "width":"100px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_color"]), value=gpa["markerc"], placeholder=gpa["markerc"], 
                                            id={'type':"markerc","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("... or write a color name", style={"margin-top":"10px", "width":"180px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["markerc_write"], placeholder=gpa["markerc_write"], type='text', id={'type':"markerc_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Fill opacity:", style={"margin-top":"10px", "width":"100px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["marker_alpha"], placeholder=gpa["marker_alpha"], type='text', id={'type':"marker_alpha","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            style={"margin-right":"5px"},
                                        ),

                                        dbc.Label("Edge color:", style={"margin-top":"10px", "width":"100px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["edge_colors"]), value=gpa["edgecolor"], placeholder=gpa["edgecolor"], 
                                            id={'type':"edgecolor","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("... or write a color name", style={"margin-top":"10px", "width":"180px"}),
                                        dbc.Col(
                                            dcc.Input(value=gpa["edgecolor_write"], placeholder=gpa["edgecolor_write"], type='text', id={'type':"edgecolor_write","index":str(card_id)}, style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                            
                                        ),

                                    ],
                                    className="g-1",
                                    align="center",
                                ),
                                ############################################





                            ],
                        ),
                        style=card_body_style),
                        #style={"margin-top":"2px","margin-bottom":"2px"} ),
                    id={'type':"collapse-dynamic-card","index":str(card_id)},
                    is_open=False,
                ),
            ],
            style={"margin-top":"2px","margin-bottom":"2px"} 
        )

        return card

    try:

        if not groups:
            field_style_on_off='inline-block'
            #cards=[ make_card("Model Settings",0, pa, pa, cols_, field_style_on_off) ]
            pa["model_settings"]=[]
            cards=[ make_card("Plot settings",0, pa, pa) ]
        else:
            field_style_on_off= 'none'
            cards=[]
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
            groups_=df[[groups]].drop_duplicates()[groups].tolist()
            
            for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
                if filename.split(".")[-1] == "json":
                    pa_=pa["groups_settings"][i]
                    header="Plot Settings: "+str(g)
                    card=make_card(header, i, pa, pa_)
                else:
                    pa["model_settings"]=[]
                    header="Plot Settings: "+str(g)
                    card=make_card(header, i, pa, pa)
                cards.append(card)
        return cards, None, None, generate_markers_import
        
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"lifespan")
        return dash.no_update, toast, tb_str , dash.no_update
        


states=[State("xvals", "value"),
    State("yvals", "value"),
    State("censors_val", "value"),
    State("groups_value","value"),
    State("fig_width","value"),
    State("fig_height","value"),
    State("title","value"),
    State("titles","value"),
    State("xlabel","value"),
    State("xlabels","value"),
    State("ylabel","value"),
    State("ylabels","value"),
    State("show_axis","value"),
    State("axis_line_width","value"),
    State("show_ticks","value"),
    State("ticks_length","value"),
    State("ticks_direction_value", "value"),
    State("xticks_fontsize","value"),
    State("yticks_fontsize","value"),
    State("xticks_rotation","value"),
    State("yticks_rotation","value"),
    State("x_lower_limit","value"),
    State("y_lower_limit","value"),
    State("x_upper_limit","value"),
    State("y_upper_limit","value"),
    State("grid_value","value"),
    State("grid_linewidth","value"),
    #State("grid_linestyle_value")
    State("grid_color_value", "value"),
    State("grid_color_text", "value"),
    State( { "type":"linewidth_write", "index":ALL}, "value"),
    State( { "type":"linestyle_value", "index":ALL}, "value"),
    State( { "type":"line_color_value", "index":ALL}, "value"),
    State( { "type":"linecolor_write", "index":ALL}, "value"),
    State( { "type":"model_settings",  "index":ALL}, "value"),
    State(  {"type":"ci_linewidth_write", "index":ALL}, "value"),
    State(  {"type":"ci_linestyle_value", "index":ALL}, "value"),
    State(  {"type":"ci_line_color_value", "index":ALL}, "value"),
    State(  {"type":"ci_linecolor_write", "index":ALL}, "value"),
    State(  {"type":"ci_alpha","index":ALL}, "value"),
    State(  { "type":"censor_marker_value", "index":ALL}, "value"),
    State(  {"type":"censor_marker_size_val", "index":ALL}, "value"),
    State(  {"type":"markerc", "index":ALL}, "value"),
    State(  {"type":"markerc_write", "index":ALL}, "value"),
    State( { "type":"edge_linewidth", "index":ALL}, "value"),
    State( { "type":"edgecolor", "index":ALL}, "value"),
    State( { "type":"edgecolor_write", "index":ALL}, "value"),
    State( { "type":"marker_alpha",  "index":ALL}, "value")
]


@dashapp.callback( 
    Output('fig-output', 'children'),
    Output( 'toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    #Output('download-pdf-div', 'style'),
    #Output('save-excel-div', 'style'),
    Output('export-session','data'),
    Output('save-excel', 'data'),
    Input("submit-button-state", "n_clicks"),
    Input("export-filename-download","n_clicks"),
    Input("save-session-btn","n_clicks"),
    Input("saveas-session-btn","n_clicks"),
    Input("excel-filename-download","n_clicks"),
    [ State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('export-filename','value'),
    State('excel-filename','value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,save_excel_btn,session_id,contents,filename,last_modified,export_filename, excel_filename,upload_data_text, *args):
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
        df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
        
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

        session_data={ "session_data": {"app": { "lifespan": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION

        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"lifespan")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, download_buttons_style_hide, None, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="lifespan.json"
        export_filename=secure_filename(export_filename)
        if export_filename.split(".")[-1] != "json":
            export_filename=f'{export_filename}.json'  

        def write_json(export_filename,session_data=session_data):
            export_filename.write(json.dumps(session_data).encode())
            # export_filename.seek(0)

        return dash.no_update, None, None, None, dcc.send_bytes(write_json, export_filename), dash.no_update

    if button_id == "save-session-btn" :
        try:
            if filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None,  None, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"lifespan")
            return dash.no_update, toast, None, tb_str, None, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        print(session_data)
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "excel-filename-download":
        eventlog = UserLogging(email=current_user.email,action="download lifespan")
        db.session.add(eventlog)
        db.session.commit()

        if not excel_filename:
            excel_filename=secure_filename("lifespan_results.%s.xlsx" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        excel_filename=secure_filename(excel_filename)
        if excel_filename.split(".")[-1] != "xlsx":
            excel_filename=f'{excel_filename}.xlsx'  

        import io
        output = io.BytesIO()
        writer= pd.ExcelWriter(output)

        if pa["groups_value"]:
            df,fig,cph_coeff_,cph_stats=make_figure(df,pa)

            df.to_excel(writer, sheet_name = 'SurvivalAnalysis', index = False)
            cph_stats.to_excel(writer, sheet_name="CoxPH.Stats", index=False)
            cph_coeff_.to_excel(writer, sheet_name="CoxPH.Coeff", index=False)

        else:
            df,fig=make_figure(df,pa)

            df.to_excel(writer, sheet_name = 'SurvivalAnalysis', index = False)
        
        writer.save()
        data=output.getvalue()
        return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(data, excel_filename)
    
    try:

        tab1_btn=html.Div( 
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
                            style={"max-width":"150px","width":"100%","margin":"4px", 'display': 'inline-block'} # 'none' / 'inline-block'
                        )

        tab2_btn=html.Div( 
                            [
                                dbc.Button(
                                    html.Span(
                                        [ 
                                            html.I(className="far fa-lg fa-save"),
                                            " Results (xlsx)" 
                                        ]
                                    ),
                                    id='save-excel-btn', 
                                    style={"max-width":"150px","width":"100%"},
                                    color="secondary"
                                ),
                                dcc.Download(id='save-excel')
                            ],
                            id="save-excel-div",
                            style={"max-width":"150px","width":"100%","margin":"4px", 'display':'inline-block'} # 'none' / 'inline-block'
                        )

        tab3_btn=html.Div( 
                            [
                                dbc.Button(
                                    html.Span(
                                        [ 
                                            html.I(className="far fa-lg fa-save"),
                                            " Results (xlsx)" 
                                        ]
                                    ),
                                    id='save-excel-btn3', 
                                    style={"max-width":"150px","width":"100%"},
                                    color="secondary"
                                ),
                                dcc.Download(id='save-excel')
                            ],
                            id="save-excel-div3",
                            style={"max-width":"150px","width":"100%","margin":"4px", 'display':'inline-block'} # 'none' / 'inline-block'
                        )

        tab4_btn=html.Div( 
                            [
                                dbc.Button(
                                    html.Span(
                                        [ 
                                            html.I(className="far fa-lg fa-save"),
                                            " Results (xlsx)" 
                                        ]
                                    ),
                                    id='save-excel-btn4', 
                                    style={"max-width":"150px","width":"100%"},
                                    color="secondary"
                                ),
                                dcc.Download(id='save-excel')
                            ],
                            id="save-excel-div4",
                            style={"max-width":"150px","width":"100%","margin":"4px", 'display':'inline-block'} # 'none' / 'inline-block'
                        )



        if pa["groups_value"]:
            df,fig,cph_coeff_,cph_stats=make_figure(df,pa)

            fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
            fig=dcc.Graph(figure=fig,config=fig_config,  id="graph") 

            df_ = make_table(df, "sa_table", fixed_columns = False)
            cph_coeff = make_table(cph_coeff_, "cph_coefficiants", fixed_columns = False)
            cph_stats_ = make_table(cph_stats, "cph_stats", fixed_columns = False)

            fig = dcc.Tabs([
            dcc.Tab([fig, tab1_btn ], label = "Lifespan Curve", id = "tab-lifespanCurve") ,
            dcc.Tab([df_, tab2_btn ], label = "Survival Analysis Table", id = "tab-saTable"),
            dcc.Tab([cph_stats_, tab3_btn ], label = "CoxPH Model Statistics", id = "tab-cphTable_stats"),
            dcc.Tab([cph_coeff, tab4_btn], label = "CoxPH Model Coefficients", id = "tab-cphTable_coeff")
            ])

        else:
            df,fig=make_figure(df,pa)

            fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
            fig=dcc.Graph(figure=fig,config=fig_config,  id="graph") 

            sa_table = make_table(df, "survivalanalysis_table", fixed_columns = False)
            
            fig = dcc.Tabs([
            dcc.Tab([fig, tab1_btn ], label = "Lifespan Curve", id = "tab-lifespanCurve"),
            dcc.Tab([sa_table, tab2_btn ], label = "Survival Analysis Table", id = "tab-saTable"),
            ])
            
       
        # # import plotly.graph_objects as go
        # fig = go.Figure( )
        # fig.update_layout( )
        # fig.add_trace(go.Scatter(x=[1,2,3,4], y=[2,3,4,8]))
        # fig.update_layout(
        #         title={
        #             'text': "Demo plotly title",
        #             'xanchor': 'left',
        #             'yanchor': 'top' ,
        #             "font": {"size": 25, "color":"black"  } } )

        #fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
        #fig=dcc.Graph(figure=fig,config=fig_config,  id="graph") 
        

        # changed
        # return fig, None, session_data, None, download_buttons_style_show
        # as session data is no longer required for downloading the figure

        return fig, None, None, None, None, None #download_buttons_style_hide, download_buttons_style_hide
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"lifespan")
        print(tb_str)
        #print(toast)
        return dash.no_update, toast, session_data, tb_str, None, None  #download_buttons_style_hide, download_buttons_style_hide


@dashapp.callback(
    Output('excel-filename-modal', 'is_open'),
    [ Input('save-excel-btn',"n_clicks"),Input("excel-filename-download", "n_clicks"), Input('save-excel-btn3',"n_clicks"), Input('save-excel-btn4',"n_clicks")],
    [ State("excel-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_excel_filename(n1, n2,n3,n4, is_open):
    if n1 or n2 or n3 or n4:
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
        pdf_filename="lifespan.pdf"
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

    eventlog = UserLogging(email=current_user.email,action="download figure lifespan")
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

        ask_for_help(tb_str,current_user, "lifespan", session_data)

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