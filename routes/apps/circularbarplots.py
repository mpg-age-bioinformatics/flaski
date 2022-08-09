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
from pyflaski.circularbarplots import make_figure, figure_defaults
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

dashapp = dash.Dash("circularbarplots",url_base_pathname=f'{PAGE_PREFIX}/circularbarplots/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit circularbarplots")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Circular bars plot",current_user),
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
                                    dbc.Label("Angular Values", style={"margin-bottom":"2px"}),
                                    dcc.Dropdown( placeholder="Angle column", id='angvals', multi=False)
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
                                    dbc.Label("Radial Values", style={"margin-bottom":"2px", "margin-top":"10px"} ),
                                    dcc.Dropdown( placeholder="Radial column", id='radvals', multi=False)
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
                                    dbc.Label("Bar Groups", style={"margin-bottom":"2px", "margin-top":"10px"} ),
                                    dcc.Dropdown(placeholder="Groups column", id='groupval', multi=False)
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
                                    dbc.Row(
                                        [
                                            dbc.Label("Title color:",html_for="title_color", style={"margin-top":"10px", "width":"90px"}), #"margin-top":"8px",
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_colors"]), value=pa["title_color"], placeholder=pa["title_color"], 
                                                id='title_color', multi=False, clearable=False, style={"margin-top":"5px", "width":"167px"}),
                                                
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
                                dbc.Button( "Plot Settings", color="black", id={'type':"dynamic-card","index":"plot settings"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Barmode:",html_for='barmode_val',style={"width":"120px","margin-top":"10px","text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["barmode"]), value=pa["barmode_val"], placeholder=pa["barmode_val"], 
                                                    id='barmode_val', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Normalisation:",html_for='barnorm_val',style={"width":"120px","margin-top":"10px","text-align":"left"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["barnorm"]), value=pa["barnorm_val"], placeholder=pa["barnorm_val"], 
                                                    id='barnorm_val', multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                    #style={"margin-right":"5px"} 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Start direction:",html_for='direction_val',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["direction"]), value=pa["direction_val"], placeholder=pa["direction_val"], 
                                                    id='direction_val', multi=False, clearable=False, style={"margin-top":"5px","width":"100%"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Start angle:",html_for='start_angle',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["start_angle"],id='start_angle', placeholder=pa["start_angle"], type='text', style={"height":"35px", "margin-top":"5px", "width":"100%"}) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Plot font size:",html_for='plot_font',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["plot_font_sizes"]), value=pa["plot_font"], placeholder=pa["plot_font"], 
                                                    id='plot_font', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Polar bargap:",html_for='polar_bargap',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["polar_bargaps"]), value=pa["polar_bargap"], placeholder=pa["polar_bargap"], 
                                                    id='polar_bargap', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Central circle:",html_for='polar_hole',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["polar_holes"]), value=pa["polar_hole"], placeholder=pa["polar_hole"], 
                                                    id='polar_hole', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Paper color:",html_for='paper_bgcolor',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["paper_bgcolors"]), value=pa["paper_bgcolor"], placeholder=pa["paper_bgcolor"], 
                                                    id='paper_bgcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [   
                                                dbc.Label("Bars layout:",html_for='polar_barmode',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["polar_barmodes"]), value=pa["polar_barmode"], placeholder=pa["polar_barmode"], 
                                                    id='polar_barmode', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"},
                                                ),

                                                dbc.Label("Background:",html_for='polar_bgcolor',style={"width":"120px","margin-top":"10px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["polar_bgcolors"]), value=pa["polar_bgcolor"], placeholder=pa["polar_bgcolor"], 
                                                    id='polar_bgcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
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
                html.Div(id="marker-cards"),
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
                                dbc.Form(
                                    [ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Background:",html_for='legend_bgcolor', style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_colors"]), value=pa["legend_bgcolor"], placeholder=pa["legend_bgcolor"], 
                                                    id='legend_bgcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Border:",html_for='legend_bordercolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_colors"]), value=pa["legend_bordercolor"], placeholder=pa["legend_bordercolor"], 
                                                    id='legend_bordercolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                ),

                                            ],
                                            align="center",
                                            className="g-1",
                                        ),
                                        #################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Borderwidth:",html_for='legend_borderwidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["legend_borderwidth"],id='legend_borderwidth', placeholder=pa["legend_borderwidth"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Orientation:",html_for='legend_orientation', style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_orientations"]), value=pa["legend_orientation"], placeholder=pa["legend_orientation"], 
                                                    id='legend_orientation', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Label font:",html_for='legend_title_font',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_title_sizes"]), value=pa["legend_title_font"], placeholder=pa["legend_title_font"], 
                                                    id='legend_title_font', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"},
                                                ),
                                                dbc.Label("Title font:",html_for='legend_text_font',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["legend_text_sizes"]), value=pa["legend_text_font"], placeholder=pa["legend_text_font"], 
                                                    id='legend_text_font', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        
                                     
                                        ######## END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"legend"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Angular Axis", color="black", id={'type':"dynamic-card","index":"angular axis"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        dbc.Row(
                                            [
                                                #dbc.Label("Axis:",html_for="show_axis", width=2),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' Grid   ', 'value': 'angular_grid'},
                                                            {'label': ' Line   ', 'value': 'angular_line'},
                                                            {'label': ' Ticklabels   ', 'value': 'angular_ticklabels'},
                                                            
                                                        ],
                                                        value=["angular_ticklabels"],
                                                        labelStyle={'display': 'inline-block', "margin-right":"110px"},#,"height":"35px"}, "margin-right":"110px",
                                                        style={"height":"35px","margin-top":"10px", "width":"100%" },
                                                        #inputStyle={"margin-right": "20px"},
                                                        id="angular_features"
                                                    ),
                                                )

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Grid color:",html_for='angular_gridcolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["angular_gridcolors"]), value=pa["angular_gridcolor"], placeholder=pa["angular_gridcolor"], 
                                                    id='angular_gridcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Grid width:",html_for='angular_gridwidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["angular_gridwidth"],id='angular_gridwidth', placeholder=pa["angular_gridwidth"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Line color:",html_for='angular_linecolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["angular_linecolors"]), value=pa["angular_linecolor"], placeholder=pa["angular_linecolor"], 
                                                    id='angular_linecolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Line width:",html_for='angular_linewidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["angular_linewidth"],id='angular_linewidth', placeholder=pa["angular_linewidth"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick color:",html_for='angular_tickcolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["angular_tickcolors"]), value=pa["angular_tickcolor"], placeholder=pa["angular_tickcolor"], 
                                                    id='angular_tickcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Tick length:",html_for='angular_ticklen',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["angular_ticklen"],id='angular_ticklen', placeholder=pa["angular_ticklen"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick angle:",html_for='angular_tickangle',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["angular_tickangle"],id='angular_tickangle', placeholder=pa["angular_tickangle"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                style={"margin-right":"5px"}
                                                
                                                ),
                                                dbc.Label("Tick width:",html_for='angular_tickwidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["angular_tickwidth"],id='angular_tickwidth', placeholder=pa["angular_tickwidth"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick direction:",html_for='angular_ticks',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["angular_tickDirections"]), value=pa["angular_ticks"], placeholder=pa["angular_ticks"], 
                                                    id='angular_ticks', multi=False, clearable=False, style={"width":"140px", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################

                                        ######## END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"angular axis"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Radial Axis", color="black", id={'type':"dynamic-card","index":"radial axis"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                dbc.Form(
                                    [ 
                                        dbc.Row(
                                            [
                                                #dbc.Label("Axis:",html_for="show_axis", width=2),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' Grid   ', 'value': 'radial_grid'},
                                                            {'label': ' Line   ', 'value': 'radial_line'},
                                                            {'label': ' Visibility   ', 'value': 'radial_visibility'},
                                                            {'label': ' Ticklabels   ', 'value': 'radial_ticklabels'}
                                                            
                                                        ],
                                                        value=["radial_visibility"],
                                                        labelStyle={'display': 'inline-block',"margin-right":"60px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"10px", "width":"100%"},
                                                        id="radial_features"
                                                    ),
                                                )

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        #################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Grid color:",html_for='radial_gridcolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["radial_gridcolors"]), value=pa["radial_gridcolor"], placeholder=pa["radial_gridcolor"], 
                                                    id='radial_gridcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Grid width:",html_for='radial_gridwidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_gridwidth"],id='radial_gridwidth', placeholder=pa["radial_gridwidth"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Line color:",html_for='radial_linecolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["radial_linecolors"]), value=pa["radial_linecolor"], placeholder=pa["radial_linecolor"], 
                                                    id='radial_linecolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Line width:",html_for='radial_linewidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_linewidth"],id='radial_linewidth', placeholder=pa["radial_linewidth"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Radial angle:",html_for='radial_angle',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_angle"],id='radial_angle', placeholder=pa["radial_angle"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) ,
                                                style={"margin-right":"5px"} 
                                                
                                                ),
                                                dbc.Label("Tick angle:",html_for='radial_tickangle',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_tickangle"],id='radial_tickangle', placeholder=pa["radial_tickangle"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick length:",html_for='radial_ticklen',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_ticklen"],id='radial_ticklen', placeholder=pa["radial_ticklen"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                style={"margin-right":"5px"}
                                                
                                                ),
                                                dbc.Label("Tick width:",html_for='radial_tickwidth',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                dcc.Input(value=pa["radial_tickwidth"],id='radial_tickwidth', placeholder=pa["radial_tickwidth"], type='text', style={"height":"35px","width":"100%", "margin-top":"5px"} ) , 
                                                
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Tick color:",html_for='radial_tickcolor',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["radial_tickcolors"]), value=pa["radial_tickcolor"], placeholder=pa["radial_tickcolor"], 
                                                    id='radial_tickcolor', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Label("Tick direction:",html_for='radial_tickside',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["radial_ticksides"]), value=pa["radial_tickside"], placeholder=pa["radial_tickside"], 
                                                    id='radial_tickside', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ####################################

                                        ######## END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"radial axis"},
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
                                    dcc.Input(id='pdf-filename', value="circularbarplots.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="circularbarplots.json", type='text', style={"width":"100%"})
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
    "groupval",
    "fig_width",
    "fig_height",
    "title",
    "titles",
    "title_color",
    "barmode_val",
    "barnorm_val",
    "direction_val",
    "start_angle",
    "plot_font",
    "legend_bgcolor",
    "legend_bordercolor",
    "legend_borderwidth",
    "legend_title_font",
    "legend_text_font",
    "legend_orientation",
    "polar_bargap",
    "polar_barmode",
    "polar_bgcolor",
    "polar_hole",
    "paper_bgcolor",
    "angular_features",
    "angular_gridcolor",
    "angular_gridwidth",
    "angular_linecolor",
    "angular_linewidth",
    "angular_tickcolor",
    "angular_ticklen",
    "angular_tickwidth",
    "angular_tickangle",
    "angular_ticks",
    "radial_features",
    "radial_gridcolor",
    "radial_gridwidth",
    "radial_linecolor",
    "radial_linewidth",
    "radial_angle",
    "radial_tickangle",
    "radial_ticklen",
    "radial_tickwidth",
    "radial_tickcolor",
    "radial_tickside"
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ Output('angvals', 'options'),
    Output('radvals', 'options'),
    Output('groupval', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Output('angvals', 'value'),
    Output('radvals', 'value')] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "circularbarplots")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            angvals=app_data['pa']["angvals"]
            radvals=app_data['pa']["radvals"]
            
            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"circularbarplots")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            angvals=cols[2]
            radvals=cols[0]
            
            
        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )

        return [ cols_, cols_, cols_, upload_text, None, None,  angvals, radvals] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        print(tb_str)
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"circularbarplots")
        print(toast)
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs
   

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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "circularbarplots")
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
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"circularbarplots")
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
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"circularbarplots")
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
        df=parse_table(contents,filename,last_modified,current_user.id,cache,"circularbarplots")
        
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

        session_data={ "session_data": {"app": { "circularbarplots": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"circularbarplots")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="circularbarplots.json"
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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"circularbarplots")
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"circularbarplots")
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
        pdf_filename="circularbarplots.pdf"
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

    eventlog = UserLogging(email=current_user.email,action="download figure circularbarplots")
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

        ask_for_help(tb_str,current_user, "circularbarplots", session_data)

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