from urllib import response
from plotly import optional_imports
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
from pyflaski.heatmap import make_figure, figure_defaults
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

dashapp = dash.Dash("heatmap",url_base_pathname=f'{PAGE_PREFIX}/heatmap/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit heatmap")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Heatmap",current_user),
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
                                    dbc.Label("Row Names",style={"margin-bottom": "0px"}),
                                    dcc.Dropdown( placeholder="Row names column", id='xvals', multi=False)
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
                                    dbc.Label("Data Columns",style={"margin-bottom": "0px"} ),
                                    dcc.Dropdown( placeholder="Sample columns", id='yvals', multi=True)
                                ],
                                style={"margin-top": "10px"}
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
                                    dbc.Label("Rows" ,style={"margin-bottom": "0px"}),
                                    dcc.Dropdown(placeholder="Row values", id='findrow', multi=True  , value=pa["findrow"] )
                                ],
                                style={"margin-top": "10px"}
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

                                            dbc.Label("Width",html_for="fig_width", style={"margin-top":"10px","width":"64px",}),
                                            dbc.Col(
                                                dcc.Input(value=pa["fig_width"], id='fig_width', placeholder="eg. 600", type='text' , style={"height":"35px","width":"100%","margin-top":"5px"} ),
                                                style={"margin-right":"5px"}
                                            ),
                                            dbc.Label("Height", html_for="fig_height",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"left"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["fig_height"], id='fig_height', placeholder="eg. 600", type='text',style={"height":"35px","width":"100%", "margin-top":"5px"}) ,
                                                
                                            ),
        
                                        ],
                                        className="g-1",
                                        align="center",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Title", html_for="title", style={"margin-top":"10px","width":"64px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder=pa["title"], type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) , 
                                                style={"margin-right":"5px"},
                                            ),
                                            dbc.Label("size", html_for="title_size_value", style={"text-align":"left","margin-left":"5px","margin-top":"10px","width":"64px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["title_size_value"], placeholder="size", 
                                                id='title_size_value', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px"}),
                                            )
                                        ],
                                        className="g-1",
                                        justify="center"
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
                                dbc.Button( "Cluster", color="black", id={'type':"dynamic-card","index":"cluster"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                                dbc.Label("Clusters:",html_for='show_clusters',style={"width":"280px"}),
                                                dbc.Col(
                                                    
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label' : 'Columns   ' , 'value': 'col_cluster'},
                                                            {'label' : 'Rows   ' , 'value': 'row_cluster'}
                                                        ],
                                                        value=pa["show_clusters"],
                                                        #inputStyle={"margin-right": "3px"},
                                                        labelStyle={'display': 'inline-block',"margin-right":"55px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"10px", "width":"100%"},
                                                        id="show_clusters"
                                                    ),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                    ############################################
                                        dbc.Row(
                                                [
                                                    dbc.Label("Cluster distance values:", html_for="dendogram_dist", style={"width":"280px", "margin-top":"10px"}), #"width":"64px"
                                                    dbc.Col(
                                                        dcc.Checklist(options=[ {'label' : 'Columns' , 'value':'col_dendogram_dist'},
                                                                                {'label' : 'Rows' , 'value':'row_dendogram_dist'}
                                                        ],
                                                        value=pa["dendogram_dist"],
                                                        #inputStyle={"margin-right": "3px"},
                                                        labelStyle={'display': 'inline-block',"margin-right":"55px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"10px", "width":"100%"},
                                                        id='dendogram_dist',
                                                        ) ,
                                                    ),
                                                ],
                                                className="g-1",
                                                justify="center",
                                            ),

                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Distance cutoff for cluster definition:", style={"margin-top":"5px"}),
                                                ),
                                            ],
                                            className="g-1",
                                            justify="start",
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Columns:", html_for="col_color_threshold", style={"margin-top":"5px", "width":"120px"}),
                                                    #width=3,
                                                    #style={"textAlign":"left","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    
                                                    dcc.Input(value=pa["col_color_threshold"],id='col_color_threshold', placeholder="", type='text',  style={"height":"35px", "width":"100%", "margin-top":"5px"} ) ,
                                                    style={"margin-right":"5px"}
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Rows:", html_for="row_color_threshold", style={"margin-top":"5px", "width":"120px"}),
                                                    #width=3,
                                                    #style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["row_color_threshold"],id='row_color_threshold', placeholder="", type='text',  style={"height":"35px", "width":"100%", "margin-top":"5px"}  ) ,
                                                    #width=3,
                                                )
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                    ############################################ 

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Dendogram-to-figure ratio:", style={"margin-top":"5px"}),
                                                ),
                                            ],
                                            className="g-1",
                                        ),

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Columns:", html_for="row_dendogram_ratio", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"left","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["row_dendogram_ratio"], id='row_dendogram_ratio', placeholder="", type='text', style=card_input_style ) ,
                                                    width=3
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Rows:", html_for="col_dendogram_ratio", style={"margin-top":"5px"}),
                                                    width=3,
                                                    style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Input(value=pa["col_dendogram_ratio"], id='col_dendogram_ratio', placeholder="", type='text', style=card_input_style ) ,
                                                    width=3
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                    ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Method:",html_for='method_value', style={"width":"80px","margin-top":"10px","text-align":"left"}),
                                                    #width=3,
                                                    #style={"textAlign":"left","padding-right":"2px"}
                                                ),                                               
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["method"]), value=pa["method_value"], placeholder=pa["method_value"], id='method_value' , 
                                                    multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"}),
                                                    style={"margin-right":"5px"},
                                                    #width=3,    
                                                ),
                                                dbc.Col(
                                                    dbc.Label("Distance:",html_for='distance_value',style={"width":"80px","margin-top":"10px","text-align":"left"}), 
                                                    #width=3,
                                                    #style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["distance"]), value=pa["distance_value"], id="distance_value",placeholder=pa["distance_value"],
                                                     multi=False, clearable=False, style={"width":"100%","margin-top":"5px","text-align":"left"} ),
                                                    #width=3
                                                )
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                    ############################################

                                        
                                    
                                    # ############################################ 
                                        
                                    ######### END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"cluster"},
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
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Data transformation:", style={"margin-top":"5px"}),
                                            ]
                                        ),
   
                                        ############################################
                                        dbc.Row(
                                            [
                                                
                                                dbc.Label("add constant:", style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["add_constant"],id='add_constant', placeholder="", type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) ,
                                                    #width=3,
                                                    #style={"textAlign":"left", "margin-top":"5px"}
                                                ),
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                
                                                dbc.Label("log transform:",html_for='log_transform_value',style={"margin-top":"10px", "width":"120px"}),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["log_transform"]), value=pa["log_transform_value"], placeholder=pa["log_transform_value"], id='log_transform_value',  
                                                    multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                    
                                                dbc.Label("z-score:",html_for='zscore_value',style={"margin-top":"10px", "width":"80px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["zscore"]), value=pa["zscore_value"], id="zscore_value", placeholder=pa["zscore_value"] , 
                                                     multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"} ),
                                                    
                                                )
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Robustness percentil (0 - 100):", style={"margin-top":"10px", "width":"240px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["robust"],id='robust', placeholder="", type='text', style={"height":"35px", "width":"100%", "margin-top":"5px"} ) ,
                                                ),
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                html.Hr(style={"color":"black", "height":"1px", "width":"90%", "horizontal-align":"middle", "margin":"auto", "margin-top":"10px", "margin-bottom":"10px"},),
                                            ],
                                            className="g-0",
                                        ),

                                        ############################################ 
                                        dbc.Row(
                                            [
                                                dbc.Label("Show labels: ",html_for='show_labels', style={"margin-top":"10px", "width":"150px"}),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label' : 'Columns   ' , 'value': 'yticklabels'},
                                                            {'label' : 'Rows   ' , 'value': 'xticklabels'}
                                                        ],
                                                        value=pa["show_labels"],
                                                        #inputStyle={"margin-right": "3px"},
                                                        labelStyle={'display': 'inline-block',"margin-right":"120px"},#,"height":"35px"},
                                                        style={"height":"35px","margin-top":"10px", "width":"100%"},
                                                        id="show_labels"
                                                    ),
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),

                                        ############################################ 
                                        
                                        dbc.Row(
                                            [
                                                dbc.Label("Labels font size:", style={"margin-top":"10px", "width":"140px"}),
                                                
                                                dbc.Label("Columns:", html_for="yaxis_font_size", style={"margin-top":"10px", "width":"80px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["yaxis_font_size"], id='yaxis_font_size', placeholder="", type='text', style={"height":"35px", "width":"40px", "margin-top":"5px"} ) ,
                                                ),

                                                dbc.Label("Rows:", html_for="xaxis_font_size", style={"margin-top":"10px","width":"60px"}),
                                                dbc.Col(
                                                    dcc.Input(value=pa["xaxis_font_size"], id='xaxis_font_size', placeholder="", type='text', style={"height":"35px", "width":"40px", "margin-top":"5px"} ) ,
                                                )
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),

                                        ############################################ 
                                        dbc.Row(
                                            [
                                                html.Hr(style={"color":"black", "height":"1px", "width":"90%", "horizontal-align":"middle", "margin":"auto", "margin-top":"10px", "margin-bottom":"10px"},),
                                            ],
                                            className="g-0",
                                        ),

                                        ############################################ 

                                        dbc.Row(
                                            [
                                                dbc.Label("CMAP", html_for="colorscale", style={"margin-top":"10px", "width":"80px"}),

                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["colorscale"]), value=pa["colorscale_value"], placeholder=pa["colorscale_value"], id='colorscale_value',
                                                        multi=False, clearable=False, style={"width":"120px", "margin-top":"5px", "text-align":"left"}),
                                                        style={"margin-right":"5px"}  ,
                                                ),
                                                
                                                dbc.Label("reverse: ", html_for="reverse_color_scale", style={"margin-top":"10px", "width":"80px"}),   
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                                {'value': 'reverse_color_scale'},
                                                            ], 
                                                            
                                                            value=[], 
                                                            id="reverse_color_scale", 
                                                            style={"width":"32px","margin-top":"5px"}, 
                                                    ),
                                                ),
                                            ],
                                            className="g-1",
                                            align="center",
                                        ),

                                        ############################################ 

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("..or, explicitly define your color map:",style={"margin-top":"10px"}),
                                                    #width=3,
                                                    #style={"textAlign":"right","padding-right":"2px"}
                                                ),
                                            ],
                                            className="g-0",
                                        ),

                                        ############################################ 

                                        dbc.Row(
                                            [
                                                #dbc.Col(
                                                dbc.Label("", style={"margin-top":"10px", "width":"140px"}),
                                                #     width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Label("Lower", style={"margin-top":"10px", "width":"110px", "margin-right":"20px"}),
                                                #     width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Label("Centre", style={"margin-top":"10px", "width":"110px", "margin-right":"20px"}),
                                                #     width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                                # ),
                                                #dbc.Col(
                                                dbc.Label("Upper", style={"margin-top":"10px", "width":"110px"}),
                                                #     width=3, #,style={"padding-left":"80px" , "vertical-align": "middle"}),
                                                # ),
                                            ],
                                            className="g-1",
                                            justify="center",
                                            align="center",
                                        ),

                                        ############################################

                                        dbc.Row(
                                            [
                                                # dbc.Col(
                                                dbc.Label("Value: ", style={"margin-top":"10px", "width":"120px"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["lower_value"], id="lower_value", placeholder="", type="text",  style={"width":"130px", "margin-top":"5px", "margin-right":"5px"} ),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["center_value"], id="center_value", placeholder="", type="text", style={"width":"130px", "margin-top":"5px", "margin-right":"5px"}),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}), 
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["upper_value"], id="upper_value", placeholder="", type="text", style={"width":"130px", "margin-top":"5px"}),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                                # ),
                                            ],
                                            className="g-1",
                                           # style={"margin-top":"5px"},
                                            align="center",
                                        ),

                                        ############################################

                                        dbc.Row(
                                            [
                                                #dbc.Col(
                                                dbc.Label("Color: ",  style={"width":"120px"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["lower_color"], id="lower_color", placeholder="", type="text", style={"width":"130px", "margin-top":"10px", "margin-right":"5px"} ),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["center_color"], id="center_color", placeholder="", type="text", style={"width":"130px", "margin-top":"10px", "margin-right":"5px"} ),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                                # ),
                                                # dbc.Col(
                                                dbc.Input(value=pa["upper_color"], id="upper_color", placeholder="", type="text", style={"width":"130px", "margin-top":"10px"} ),
                                                    #style={"width":"65px", "height":"22px", "padding-left":"4px" , "vertical-align": "middle"}),
                                                # ),
                                            ],
                                            className="g-1",
                                            #style={"margin-top":"5px"},
                                            align="center",
                                        ),

                                        ############################################

                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Label("Color bar "),
                                                ),
                                            ],
                                            className="g-1",
                                        ),

                                        ############################################

                                        dbc.Row(
                                            [
                                                
                                                dbc.Label("Label:", style={"width":"80px", "margin-top":"10px"}),
                                                dbc.Col(
                                                    dbc.Input(value=pa["color_bar_label"], id="color_bar_label", placeholder="", type="text",  style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                
                                                dbc.Label("Font size:", style={"width":"80px", "margin-top":"10px"}),   
                                                dbc.Col(
                                                    dbc.Input(value=pa["color_bar_font_size"], id="color_bar_font_size", placeholder=[pa["color_bar_font_size"]], type="text", style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                    
                                                ),
                                            ],
                                            className="g-1",
                                            align="center",
                                            
                                        ),

                                        ############################################

                                        dbc.Row(
                                            [
                                                
                                                dbc.Label("Tick size:", style={"width":"80px", "margin-top":"10px"}),
                                                dbc.Col(
                                                    dbc.Input(value=pa["color_bar_ticks_font_size"], id="color_bar_ticks_font_size", placeholder=[pa["color_bar_ticks_font_size"]], type="text", style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                    style={"margin-right":"5px"}
                                                ),
                                                
                                                dbc.Label("Padding:", style={"width":"80px", "margin-top":"10px"}),
                                                dbc.Col(
                                                    dbc.Input(value=pa["color_bar_horizontal_padding"], id="color_bar_horizontal_padding", placeholder=[pa["color_bar_horizontal_padding"]], type="text", style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                    
                                                ),

                                            ],
                                            className="g-1",
                                            align="center",
                                        ),

                                    ######### END OF CARD #########        
                                    ]
                                ),
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"plot"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Find rows", color="black", id={'type':"dynamic-card","index":"find rows"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Label("Find related rows"), 
                                        ],
                                        className="g-1",
                                    ),
                                    ############################

                                    dbc.Row(
                                        [
                                            dbc.Label("Bound type:", style={"width":"120px", "margin-top":"10px"}),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["findrowtype"]), value=pa["findrowtype_value"], placeholder=pa["findrowtype_value"],
                                                id='findrowtype_value', multi=False, clearable=False, style={"width":"100%", "margin-top":"5px", "text-align":"left"} ) ,

                                            ),
                                        ],
                                        className="g-1",
                                        align="center",
                                        
                                    ),
                                    ############################

                                    dbc.Row(
                                        [
                                            dbc.Label("Lower distance bounds:", style={"width":"200px", "margin-top":"10px"}),
                                            dbc.Col(
                                                    dbc.Input(value=pa["findrowdown"], id="findrowdown", placeholder="", type="text", style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                ),     
                                        ],
                                        className="g-1",
                                        align="center",
                                        
                                    ),
                                    ############################

                                    dbc.Row(
                                        [
                                            dbc.Label("Upper distance bounds:", style={"width":"200px", "margin-top":"10px"}),
                                            dbc.Col(
                                                    dbc.Input(value=pa["findrowup"], id="findrowup", placeholder="", type="text", style={"height":"35px", "width":"100%", "margin-top":"5px"}),
                                                ),
                                        ],
                                        className="g-1",
                                        align="center",

                                    ),
                                    ############################


                                    ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"find rows"},
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
                                ],
                                style={"height":"100%"}
                            ),
                            html.Div(
                                [
                                    html.Div( id="toast-read_input_file"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"read_input_file" }), 
                                    # html.Div( id="toast-update_labels_field"  ),
                                    # dcc.Store( id={ "type":"traceback", "index":"update_labels_field" }), 
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
                                    dcc.Input(id='pdf-filename', value="heatmap.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="heatmap.json", type='text', style={"width":"100%"})
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
                    ),

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), # dbc.ModalTitle(
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='excel-filename', value="clusters.xlsx", type='text', style={"width":"100%"})
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
    'findrow',
    'fig_width',
    'fig_height',
    'title',
    'title_size_value',
    'show_clusters',
    'method_value',
    'distance_value',
    'dendogram_dist',
    'col_color_threshold',
    'row_color_threshold',
    'col_dendogram_ratio',
    'row_dendogram_ratio',
    'add_constant',
    'log_transform_value',
    'zscore_value',
    'robust',
    'show_labels',
    'xaxis_font_size',
    'yaxis_font_size',
    'colorscale_value',
    'reverse_color_scale',
    'lower_value',
    'center_value',
    'upper_value',
    'lower_color',
    'center_color',
    'upper_color',
    'color_bar_label',
    'color_bar_font_size',
    'color_bar_ticks_font_size',
    'color_bar_horizontal_padding',
    'findrowtype_value',
    'findrowdown',
    'findrowup'
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [ Output('xvals', 'options'),
    Output('yvals', 'options'),
    Output('findrow', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Output('xvals', 'value'),
    Output('yvals', 'value'),
    Output('findrow', 'children'),]+ read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "heatmap")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            xvals=app_data['pa']["xvals"]
            yvals=app_data['pa']["yvals"]
            available_rows=df[xvals].tolist()
            available_rows_=make_options(available_rows)

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"heatmap")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            xvals=cols[0]
            yvals=cols[1:]
            available_rows=df[xvals].tolist()
            available_rows_=make_options(available_rows)
            
        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )
        return [ cols_, cols_, available_rows_, upload_text, None, None,  xvals, yvals, available_rows] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        print(tb_str)
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"heatmap")
        print(toast)
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update, dash.no_update ] + pa_outputs
   


states=[State('xvals', 'value'),
    State('yvals', 'value'),
    State('findrow', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('title', 'value'),
    State('title_size_value', 'value'),
    State('show_clusters', 'value'),
    State('method_value', 'value'),
    State('distance_value', 'value'),
    State('dendogram_dist', 'value'),
    State('col_color_threshold', 'value'),
    State('row_color_threshold', 'value'),
    State('col_dendogram_ratio', 'value'),
    State('row_dendogram_ratio', 'value'),
    State('add_constant', 'value'),
    State('log_transform_value', 'value'),
    State('zscore_value', 'value'),
    State('robust', 'value'),
    State("show_labels", 'value'),
    State('xaxis_font_size', 'value'),
    State('yaxis_font_size', 'value'),  
    State('colorscale_value', 'value'),
    State('reverse_color_scale', 'value'),
    State('lower_value', 'value'),
    State('center_value', 'value'),
    State('upper_value', 'value'),
    State('lower_color', 'value'),
    State('center_color', 'value'),
    State('upper_color', 'value'),
    State('color_bar_label', 'value'),
    State('color_bar_font_size', 'value'),
    State('color_bar_ticks_font_size', 'value'),
    State('color_bar_horizontal_padding', 'value'),
    State('findrowtype_value', 'value'),
    State('findrowdown', 'value'),
    State('findrowup', 'value'),
    ]

@dashapp.callback( 
    Output('fig-output', 'children'),
    Output( 'toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    Output('save-excel-div', 'style'),
    Output('download-pdf-div', 'style'),
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
    State('excel-filename', 'value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,save_excel_btn,session_id,contents,filename,last_modified,export_filename,excel_filename,upload_data_text, *args):
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
        df=parse_table(contents,filename,last_modified,current_user.id,cache,"heatmap")
        
        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_


        session_data={ "session_data": {"app": { "heatmap": {"filename":upload_data_text, "last_modified":last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION

        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"heatmap")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, download_buttons_style_hide, None, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="heatmap.json"
        export_filename=secure_filename(export_filename)
        if export_filename.split(".")[-1] != "json":
            export_filename=f'{export_filename}.json'  

        def write_json(export_filename,session_data=session_data):
            export_filename.write(json.dumps(session_data).encode())
            # export_filename.seek(0)

        return dash.no_update, None, None, None, dash.no_update, dash.no_update, dcc.send_bytes(write_json, export_filename), None

    if button_id == "excel-filename-download":

        eventlog = UserLogging(email=current_user.email,action="download clusters")
        db.session.add(eventlog)
        db.session.commit()

        if not excel_filename:
            excel_filename=secure_filename("clusters.%s.xlsx" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        excel_filename=secure_filename(excel_filename)
        if excel_filename.split(".")[-1] != "xlsx":
            excel_filename=f'{excel_filename}.xlsx'  

        fig, clusters_cols, clusters_rows, df_=make_figure(df,pa)

        import io
        output = io.BytesIO()
        writer= pd.ExcelWriter(output)

        df_.to_excel(writer, sheet_name = 'heatmap', index = None)
        if type(clusters_cols) != type(None):
            clusters_cols.to_excel(writer,sheet_name="rows",index=None)
        if type(clusters_rows) != type(None):
            clusters_rows.to_excel(writer,sheet_name="cols",index=None)
        writer.save()
        data=output.getvalue()
        return dash.no_update, None, None, None, dash.no_update,dash.no_update, dash.no_update, dcc.send_bytes(data, excel_filename)

    if button_id == "save-session-btn" :
        try:
            if filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None, dash.no_update, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"heatmap")
            return dash.no_update, toast, None, tb_str, dash.no_update, dash.no_update, None, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    try:
        fig, clusters_cols, clusters_rows, df_=make_figure(df,pa)
        # print(clusters_cols)
        # print(clusters_rows)
        # print(df_)
        # print(pa)
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
        fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")#, responsive=True)

        # changed
        # return fig, None, session_data, None, download_buttons_style_show
        # as session data is no longer required for downloading the figure

        return fig, None, None, None, download_buttons_style_show, download_buttons_style_show, None, None
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"heatmap")
        return dash.no_update, toast, session_data, tb_str, download_buttons_style_hide, download_buttons_style_hide, None, None

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
        pdf_filename="heatmap.pdf"
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
    eventlog = UserLogging(email=current_user.email,action="download figure heatmap")
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

        ask_for_help(tb_str,current_user, "heatmap", session_data)

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