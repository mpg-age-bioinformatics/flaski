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
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
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
                                    dbc.Label("Time"),
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
                                    dbc.Label("Death" ),
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
                                    dbc.Label("Censors" ),
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
                                    dbc.Label("Groups" ),
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
                                dbc.Button( "Axes", color="black", id={'type':"dynamic-card","index":"plot settings"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                                    dcc.Input(value=pa["xlabel"],id='xlabel', placeholder=pa["xlabel"], type='text', style={"height":"35px","width":"280px", "margin-top":"5px"} ) , 
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
                                                    dcc.Input(value=pa["ylabel"],id='ylabel', placeholder=pa["ylabel"], type='text', style={"height":"35px","width":"280px", "margin-top":"5px"} ) , 
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
                                                        labelStyle={'display': 'inline-block', "margin-right":"60px"},#,"height":"35px"}, "margin-right":"110px",
                                                        style={"height":"35px","margin-top":"10px", "width":"100%" },
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
                                                            {'label': ' left   ',  'value': 'tick_left_axis'},
                                                            {'label': ' right   ', 'value': 'tick_right_axis'},
                                                            {'label': ' upper   ', 'value': 'tick_upper_axis'},
                                                            {'label': ' lower   ', 'value': 'tick_lower_axis'}
                                                            
                                                        ],
                                                        value=["tick_left_axis", "tick_lower_axis"],
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
                                                dbc.Label("... or write a color name",html_for='grid_color_value',style={"width":"180px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["grid_color_value"],id='grid_color_value', placeholder=pa["grid_color_value"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                    
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
                            id={'type':"collapse-dynamic-card","index":"plot settings"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                # html.Div(id="marker-cards"),
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
                                    )
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
        # "Conf_Interval":".off",\
        # "show_censors":".off",\
        # "ci_legend":".off",\
        # "ci_force_lines":".off",\
        # "censor_marker":ALLOWED_MARKERS,\
        # "censor_marker_value":"x",\
        # "censor_marker_size":STANDARD_SIZES,\
        # "censor_marker_size_val":"4",\
        # "censor_marker_size_cols":["select a column.."], \
        # "censor_marker_size_col":"select a column..", \
        # "marker_color":STANDARD_COLORS,\
        # "markerc":"black",\
        # "markerc_cols":["select a column.."], \
        # "markerc_col":"select a column..", \
        # "markerc_write":"",\
        # "ci_alpha",
        # "linestyle_value"
        # "linestyle_write",
        # "linewidth_cols":["select a column.."],\
        # "linewidth_col":"select a column..",\
        # "linewidth_write":"1.0",\
        # "line_colors":STANDARD_COLORS,\
        # "line_color_value":"blue",\
        # "linecolor_cols":["select a column.."],\
        # "linecolor_col":"select a column..",\
        # "linecolor_write":"",\
        # "edge_linewidths":STANDARD_SIZES,\
        # "edge_linewidth":"1",\
        # "edge_linewidth_cols":["select a column.."],\
        # "edge_linewidth_col":"select a column..",\
        # "edge_colors":STANDARD_COLORS,\
        # "edgecolor":"black",\
        # "edgecolor_cols":["select a column.."], \
        # "edgecolor_col":"select a column..", \
        # "edgecolor_write":"",\
        # "marker_alpha":"1",\
        "xlabel",
        "xlabels",
        "ylabel",
        "ylabels",
        "axis_line_width",
        #"show_axis",
        #"show_ticks",
        "ticks_direction_value",
        "ticks_length",
        "xticks_fontsize",
        "yticks_fontsize",
        "xticks_rotation",
        "yticks_rotation",
        "x_lower_limit",
        "y_lower_limit",
        "x_upper_limit",
        "y_upper_limit",
        # #"maxxticks"
        # #"maxyticks",
        "grid_value",
        # #"grid_color_value",
        # #"grid_linestyle_value"
        "grid_linewidth"
        #"grid_alpha"
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
    #Output('censors_val', 'value')  ] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "scatterplot")
            pa=app_data['pa']
            generate_markers_import=True
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"scatterplot")
            cols=df.columns.tolist()
            cols_=make_options(cols)
    else:
        cols=[]
        cols_=make_options(cols)

        
    def make_card(card_header,card_id,pa,gpa, cols_, field_style_on_off):
        card_input_style={"height":"35px","width":"100%"}
        card_input_style_dynamic={"height":"35px","width":"100%", 'display':field_style_on_off}
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

                                        dbc.Label("Fixed Styles", style={'font-weight': 'bold','display':field_style_on_off}),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [

                                        dbc.Label("Marker:",width=2),
                                    ],
                                    className="g-1",
                                ),
                            ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("shape", width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["markerstyles"]), value=gpa["marker"], placeholder="marker", id={'type':"marker","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=6
                                        ),
                                        dbc.Label("size",style={"textAlign":"right"},width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_size"]), value=gpa["markers"], placeholder="size", id={'type':"markers","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=2
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                      
                                        dbc.Label("color",width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_color"]), value=gpa["markerc"], placeholder="size", id={'type':"markerc","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                                [
                                                    dcc.Input(id={'type':"markerc_write","index":str(card_id)},value=gpa["markerc_write"], placeholder=".. or, write color name", type='text', style={"height":"35px","width":"100%"} ),
                                                ],
                                            width=6,
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("alpha",width=2),
                                        dbc.Col(
                                            dcc.Input(id={'type':"marker_alpha","index":str(card_id)}, value=gpa["marker_alpha"],placeholder="value", type='text', style={"height":"35px","width":"100%"} ),
                                            width=4
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "90%", "height" :'2px', "margin-top":"15px","margin-bottom":"15px","margin":"auto","horizontal-align":"middle"})
                                ],
                                className="g-1",
                                justify="start"),
                                ############################################
                                dbc.Row(
                                    [

                                        dbc.Label("Line:",width=2),
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=1),
                                        dbc.Label("width",width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["edge_linewidths"]), value=gpa["edge_linewidth"], placeholder="width", id={'type':"edge_linewidth","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=1),
                                        dbc.Label("color",width=2),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["edge_colors"]), value=gpa["edgecolor"], placeholder="color", id={'type':"edgecolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dcc.Input(id={'type':"edgecolor_write","index":str(card_id)}, value=gpa["edgecolor_write"], placeholder=".. or, write color name", type='text', style=card_input_style ),
                                            width=5
                                        )
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px", 'display':field_style_on_off })
                                ],
                                className="g-1",
                                justify="start"),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Dynamic marker styles", style={'font-weight': 'bold', 'display':field_style_on_off}),
                               
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Select a column and range for dynamic sizes", style={'display':field_style_on_off}),
                               
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [   dbc.Label("", width = 4, style={'display':field_style_on_off}),
                                        dbc.Col(
                                            dcc.Dropdown( options=cols_, value=gpa["markersizes_col"], id={'type':"markersizes_col","index":str(card_id)}, multi=False, style=card_input_style_dynamic ),
                                            width=8
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################################ 

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("and explicitly define your size map if necessary:",style={"margin-top":"5px",'display':field_style_on_off }),
                                            #width=3,
                                            #style={"textAlign":"right","padding-right":"2px"}
                                        ),
                                    ],
                                    className="g-0",
                                ),

                                ############################################ 

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("", style={'display':field_style_on_off}),
                                            width=4, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Label("Lower", style={'display':field_style_on_off}),
                                            width=4, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("Center", style={'display':field_style_on_off}),
                                        #     width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        # ),
                                        dbc.Col(
                                            dbc.Label("Upper", style={'display':field_style_on_off}),
                                            width=4, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    justify="center",
                                ),

                                ############################################

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Value: ", style={'display':field_style_on_off}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["lower_size_value"], id={'type':"lower_size_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off}),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                        ),
                                        # dbc.Col(
                                        #     dbc.Input(value=pa["center_size_value"], id={'type':"center_size_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off}),
                                        #     #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                        # ),
                                        dbc.Col(
                                            dbc.Input(value=pa["upper_size_value"], id={'type':"upper_size_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off}),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    style={"margin-top":"5px"},
                                    align="center",
                                ),

                                ############################################

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Size: ", style={'display':field_style_on_off}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["lower_size"], id={'type':"lower_size","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                        # dbc.Col(
                                        #     dbc.Input(value=gpa["center_size"], id={'type':"center_size","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                        #     #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        # ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["upper_size"], id={'type':"upper_size","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    style={"margin-top":"5px"},
                                    align="center",
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "90%", "height" :'2px', "margin-top":"15px","margin-bottom":"15px","margin":"auto","horizontal-align":"middle",'display':field_style_on_off})
                                ],
                                className="g-1",
                                justify="start"),
                                ############################################
                                dbc.Row(
                                    [
                                        dbc.Label("Select a column and color scale for gradient coloring", style={'display':field_style_on_off}),
                               
                                    ],
                                    className="g-1",
                                ),
                                ############################################
                                dbc.Row(
                                    [   dbc.Label("", width = 1,style={'display':field_style_on_off}),
                                        dbc.Col(
                                            dcc.Dropdown( options=cols_, value=gpa["markerc_col"], id={'type':"markerc_col","index":str(card_id)}, multi=False, clearable=True, style=card_input_style_dynamic ),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("CMAP:", html_for="colorscale", style={"margin-top":"5px",'display':field_style_on_off}),
                                            width=2,
                                            style={"textAlign":"right"},
                                        ),
                                        dbc.Col(
                                            dcc.Dropdown(options=make_options(pa["colorscale"]), value=gpa["colorscale_value"], id={'type':"colorscale_value","index":str(card_id)}, multi=False, clearable=False, style=card_input_style_dynamic ),
                                            width=3,
                                            style={"margin-top":"5px"}
                                        ),
                                        dbc.Col(
                                            dcc.Checklist(
                                                options=[
                                                    {'label': 'reverse', 'value': 'reverse_color_scale'},], value=gpa['reverse_color_scale'], id={'type':"reverse_color_scale","index":str(card_id)}, style={"margin-top":"7px",'display':field_style_on_off}, 
                                            ),
                                            width=2,
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################################ 

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("..or, explicitly define your color map:",style={"margin-top":"5px",'display':field_style_on_off}),
                                            #width=3,
                                            #style={"textAlign":"right","padding-right":"2px"}
                                        ),
                                    ],
                                    className="g-0",
                                ),

                                ############################################ 

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("", style={'display':field_style_on_off}),
                                            width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Label("Lower", style={'display':field_style_on_off}),
                                            width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Label("Center", style={'display':field_style_on_off}),
                                            width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Label("Upper", style={'display':field_style_on_off}),
                                            width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    justify="center",
                                ),

                                ############################################

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Value: ", style={'display':field_style_on_off}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["lower_value"], id={'type':"lower_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=pa["center_value"], id={'type':"center_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=pa["upper_value"], id={'type':"upper_value","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    style={"margin-top":"5px"},
                                    align="center",
                                ),

                                ############################################

                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Color: ", style={'display':field_style_on_off}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["lower_color"], id={'type':"lower_color","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["center_color"], id={'type':"center_color","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["upper_color"], id={'type':"upper_color","index":str(card_id)}, placeholder="", type="text", style={'display':field_style_on_off} ),
                                            #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                        ),
                                    ],
                                    className="g-1",
                                    style={"margin-top":"5px"},
                                    align="center",
                                ),
                                ############################################
                                dbc.Row(
                                    [   
                                        dbc.Col(
                                            dcc.Checklist(
                                                options=[
                                                    {'label': ' show legend', 'value': 'color_legend'},], value=gpa['color_legend'], id={'type':"color_legend","index":str(card_id)}, style={"margin-top":"17px",'display':field_style_on_off}, 
                                            ),
                                            width=3,
                                        ),
                                        dbc.Col(
                                            dbc.Label("Title:", html_for="colorscaleTitle", style={"margin-top":"15px",'display':field_style_on_off}),
                                            width=2,
                                            style={"textAlign":"right"},
                                        ),
                                        dbc.Col(
                                            dbc.Input(value=gpa["colorscaleTitle"], id={'type':"colorscaleTitle","index":str(card_id)}, placeholder="", type="text", style={"margin-top":"10px",'display':field_style_on_off} ),
                                            width=7
                                        ),
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
            field_style_on_off='inline-block'
            cards=[ make_card("Marker",0, pa, pa, cols_, field_style_on_off) ]
        else:
            field_style_on_off= 'none'
            cards=[]
            groups_=df[[groups]].drop_duplicates()[groups].tolist()
            for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
                if filename.split(".")[-1] == "json" and not filename in ["<from MDS app>.json", "<from PCA app>.json", "<from tSNE app>.json"]:
                    pa_=pa["groups_settings"][i]
                    card=make_card(g, i, pa, pa_, cols_,field_style_on_off)
                else:
                    card=make_card(g, i, pa, pa, cols_,field_style_on_off)
                cards.append(card)
        return cards, None, None, generate_markers_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"scatterplot")
        return dash.no_update, toast, tb_str, dash.no_update










        
   

@dashapp.callback( 
    Output('marker-cards', 'children'),
    Output('toast-generate_markers','children'),
    Output({ "type":"traceback", "index":"generate_markers" },'data'),
    Output('generate_markers-import', 'data'),
    Input('session-id', 'data'),
    Input('groupval', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('generate_markers-import', 'data'),
    )
def generate_markers(session_id,groups,contents,filename,last_modified,generate_markers_import):
    pa=figure_defaults()
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_markers_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "lifespan")
            pa=app_data['pa']
            generate_markers_import=True
            
    def make_card(card_header,card_id,pa,gpa,):
        
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
                                        dbc.Label("Bar Color:", style={"margin-top":"10px", "width":"100px"}),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["bar_colours"]), value=gpa["bar_colour_val"], placeholder="Color", id={'type':"bar_colour_val","index":str(card_id)}, multi=False, clearable=False, style={"height":"35px","width":"220px","margin-top":"5px"} ),
                                            
                                        ),
                                    ],
                                    className="g-1",
                                    align="center",
                                ), 
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
            cards=[ make_card("Bar Color",0, pa, pa) ]
        else:
            cards=[]
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
            groups_=df[[groups]].drop_duplicates()[groups].tolist()
            for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
                if filename.split(".")[-1] == "json":
                    pa_=pa["groups_settings"][i]
                    header="Bar Color: "+str(g)
                    card=make_card(header, i, pa, pa_)
                else:
                    header="Bar Color: "+str(g)
                    card=make_card(header, i, pa, pa)
                cards.append(card)
        return cards, None, None, generate_markers_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"lifespan")
        return dash.no_update, toast, tb_str, dash.no_update


states=[State('angvals', 'value'),
    State('radvals', 'value'),
    State('groupval', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('title', 'value'),
    State('titles', 'value'),
    State('title_color', 'value'),
    State('barmode_val', 'value'),
    State('barnorm_val', 'value'),
    State('start_angle', 'value'),
    State('plot_font', 'value'),
    State('legend_bgcolor', 'value'),
    State('legend_bordercolor', 'value'),
    State('legend_borderwidth', 'value'),
    State('legend_title_font', 'value'),
    State('legend_text_font', 'value'),
    State('legend_orientation', 'value'),
    State('polar_bargap', 'value'),
    State('polar_barmode', 'value'),
    State("polar_bgcolor", 'value'),
    State('polar_hole', 'value'),
    State('paper_bgcolor', 'value'),  
    State('angular_features', 'value'),
    State('angular_ticks', 'value'),
    State('angular_gridcolor', 'value'),
    State('angular_gridwidth', 'value'),
    State('angular_linecolor', 'value'),
    State('angular_linewidth', 'value'),
    State('angular_tickcolor', 'value'),
    State('angular_ticklen', 'value'),
    State('angular_tickwidth', 'value'),
    State('angular_tickangle', 'value'),
    State('radial_features', 'value'),
    State('radial_gridcolor', 'value'),
    State('radial_gridwidth', 'value'),
    State('radial_linecolor', 'value'),
    State('radial_linewidth', 'value'),
    State('radial_angle', 'value'),
    State('radial_tickangle', 'value'),
    State('radial_ticklen', 'value'),
    State('radial_tickwidth', 'value'),
    State('radial_tickcolor', 'value'),
    State('radial_tickside', 'value'),
    State( {'type': 'bar_colour_val', 'index':ALL}, 'value' )
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
        df=parse_table(contents,filename,last_modified,current_user.id,cache,"lifespan")
        
        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_

        if pa["groupval"]:
            groups=df[[ pa["groupval"] ]].drop_duplicates()[ pa["groupval"] ].tolist()
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
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"lifespan")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"lifespan")
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"lifespan")
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