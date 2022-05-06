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
from pyflaski.dendrogram import make_figure, figure_defaults
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

dashapp = dash.Dash("dendrogram",url_base_pathname=f'{PAGE_PREFIX}/dendrogram/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    eventlog = UserLogging(email=current_user.email, action="visit dendrogram")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Dendrogram",current_user),
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
                ############################################
                dbc.Row(
                    [
                        dbc.Label("Data Columns", width=4),
                        dbc.Col(
                            dcc.Dropdown( placeholder="select data columns", id='datacols', multi=True),
                            width=8
                        )
                    ],
                    className="g-1",
                    style={"margin-top":"2px"}
                ),
                ############################################
                dbc.Row(
                    [
                        dbc.Label("Labels", width=4),
                        dbc.Col(
                            dcc.Dropdown( placeholder="", id='labelcol', multi=False),
                            width=8
                        )
                    ],
                    className="g-1",
                    style={"margin-top":"2px"}
                ),
                ############################################
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
                                            dbc.Label("Layout"), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [

                                            dbc.Label("Width",html_for="fig_width", style={"margin-top":"10px","text-align":"right","width":"64px",}), #"height":"35px",
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
                                        style={"margin-top":"1px"}
                                    ),

                                    ############################
                                    dbc.Row(
                                        [

                                            dbc.Label("Page c.",html_for="paper_bgcolor", style={"margin-top":"10px","text-align":"right","width":"64px"}), #"height":"35px",
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["paper_bgcolor"], placeholder="paper_bgcolor", id='paper_bgcolor', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
                                            dbc.Label("BKG c.", html_for="plot_bgcolor",style={"margin-left":"5px","margin-top":"10px","width":"64px","text-align":"right"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["plot_bgcolor"], placeholder="plot_bgcolor", id='plot_bgcolor', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
        
                                        ],
                                        className="g-1",
                                    ),
                                    dbc.Row(
                                        [
                                            # dbc.Col(
                                            dbc.Label("Legend",html_for="show_legend", style={"margin-top":"5px","width":"64px"}),
                                                # width=2,
                                                # style={"textAlign":"right","padding-right":"2px"}
                                            # ),
                                            dbc.Col(
                                                dcc.Checklist(options=[ {'value':'show_legend'} ], value=pa["show_legend"], id='show_legend', style={"margin-top":"6px","height":"35px"} ),
                                                # width =3
                                            )
                                        ],
                                        className="g-0"
                                    ),                     
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                    ],
                                    className="g-1",
                                    ),
                                   ############################
                                    dbc.Row(
                                            dbc.Label("Title"), #"height":"35px",
                                    ),
                                   ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Input(value=pa["title"],id='title', placeholder="title", type='text', style={"height":"35px","min-width":"169px","width":"100%"} ) ,
                                                # style={"margin-right":"5px"},
                                            )
                                        ],
                                        className="g-1"
                                    ),                                
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Font", style={"margin-top":"10px"}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Family",html_for="title_fontfamily", style={"margin-top":"5px"}),
                                                style={"textAlign":"right"},#,"padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["title_fontfamily"], placeholder="font", id='title_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                width=10
                                            ),
                                        ],
                                        className="g-1"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Size",html_for="title_fontsize", style={"text-align":"right", "margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["fontsizes"]), value=pa["title_fontsize"], placeholder="title_fontsize", id='title_fontsize', multi=False, clearable=False, style=card_input_style),
                                                width=4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Color",html_for="title_fontcolor", style={"text-align":"right","margin-left":"5px","margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["title_fontcolor"], placeholder="title_fontcolor", id='title_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                width=4
                                            )
                                        ],
                                        className="g-1",
                                    ),                                
                                    ############################
                                    dbc.Row(
                                            dbc.Label("X coordinates", style={"margin-top":"10px"}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                            dbc.Label("Reference",html_for="xref", style={"margin-top":"5px"}),#,"text-align":"right","width":"74px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["references"]), value=pa["xref"], placeholder="xref", id='xref', multi=False, clearable=False, style=card_input_style),
                                                width=4
                                            ),
                                        ],
                                        className="g-1",
                                    ),                                
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Position",html_for="x", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["x"],id='x', placeholder="x", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("Anchor",html_for="title_xanchor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_xanchors"]), value=pa["title_xanchor"], placeholder="title_xanchor", id='title_xanchor', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            )
                                        ],
                                        className="g-1",
                                    ),                                
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Y coordinates", style = {'margin-top' : '10px'}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Reference",html_for="yref", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["references"]), value=pa["yref"], placeholder="yref", id='yref', multi=False, clearable=False, style=card_input_style),
                                                width=4
                                            ),
                                        ],
                                        className="g-1"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Position",html_for="y", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=4
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["y"],id='y', placeholder="y", type='text', style=card_input_style) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("Anchor",html_for="title_yanchor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["title_yanchors"]), value=pa["title_yanchor"], placeholder="title_yanchor", id='title_yanchor', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            )
                                        ],
                                        className="g-1"
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
                                dbc.Button( "Dendrogram plot", color="black", id={'type':"dynamic-card","index":"dendrogramplot"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                            dbc.Col(
                                                dbc.Label("Fill color",html_for="color_value", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["color_value"], placeholder="color_value", id='color_value', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label(".. or write",html_for="color_rgb", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='color_rgb', placeholder="", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Orientation",html_for="orientation", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["orientations"]), value=pa["orientation"], placeholder="orientation", id='orientation', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Labels",html_for="labels", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='labels', placeholder="", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Hover text",html_for="hover_text", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='hover_text', placeholder="", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Distance",html_for="dist_func", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["dist_funcs"]), value=pa["dist_func"], placeholder="dist_func", id='dist_func', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Threshold",html_for="color_threshold", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='color_threshold', placeholder="", type='text',style={"height":"35px","width":"100%"}  ) ,
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Linkage",html_for="link_func", style={"margin-top":"10px","text-align":"right"}), 
                                                width = 4, #"height":"35px",
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["link_funcs"]), value=pa["link_func"], placeholder="link_func", id='link_func', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                            ),
                                        ],
                                        className="g-1",
                                        style={"margin-top":"1px"}
                                    ),

                                    ############################


                                    ############################
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"dendrogramplot"},
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
                                [
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("X label",html_for="xlabel", width="auto"),#, style={"margin-top":"5px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["xlabel"],id='xlabel', placeholder="", type='text', style={"width":"100%"}) ,
                                            ),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Y label",html_for="ylabel", width="auto"), #, style={"margin-top":"5px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["ylabel"],id='ylabel', placeholder="", type='text', style={"width":"100%"}) ,
                                            ),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Color",html_for="label_fontcolor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["label_fontcolor"], placeholder="label_fontcolor", id='label_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 5
                                            ),
                                            dbc.Col(
                                                dbc.Label("Size",html_for="label_fontsize", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["label_fontsize"], placeholder="label_fontsize", id='label_fontsize', multi=False, clearable=False, style=card_input_style),
                                                width = 2
                                            )
                                       ],
                                        className="g-1",
                                        justify="start"
                                    ),                                
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Family",html_for="label_fontfamily", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["label_fontfamily"], placeholder="label_fontfamily", id='label_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                width = 9
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
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Fill color",html_for="axis_line_color", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown(options=make_options(pa["colors"]), value=pa["axis_line_color"], placeholder="axis_line_color", id='axis_line_color', multi=False, clearable=False, style=card_input_style),
                                                width=5
                                            ),
                                            dbc.Col(
                                                dbc.Label("Width",html_for="axis_line_width", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["axis_line_width"],id='axis_line_width', placeholder="", type='text', style=card_input_style),
                                                width=2
                                            ),
                                            dbc.Label("",width=4),                                            
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                    ],
                                    className="g-1",
                                    justify="start"),
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Ticks"), #"height":"35px",
                                    ),
                                    ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Location:",html_for="tick_axis",width=3),
                                                dbc.Col(
                                                    dcc.Checklist(
                                                        options=[
                                                            {'label': ' X   ', 'value': 'tick_lower_axis'},
                                                            {'label': ' Y   ', 'value': 'tick_left_axis'},
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
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Direction",html_for="ticks_direction_value", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["ticks_direction"]), value=pa["ticks_direction_value"], placeholder="ticks_direction_value", id='ticks_direction_value', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("Color",html_for="ticks_color",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["ticks_color"], placeholder="ticks_color", id='ticks_color', multi=False, clearable=False, style={"height":"35px","width":"100%",'display': 'inline-block'}),#, style=card_input_style),
                                                width=4
                                            ),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Width",html_for="ticks_line_width", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["ticks_line_width"],id='ticks_line_width', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(    
                                                dbc.Label("Length",html_for="ticks_length",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["ticks_length"],id='ticks_length', placeholder="", type='text', style=card_input_style),
                                                width = 4
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("X ticks",style={"margin-top":"5px"}),#, style={"margin-top":"10px"}),
                                                style={"textAlign":"left"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("font size",html_for="xticks_fontsize",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["xticks_fontsize"],id='xticks_fontsize', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("rotation",html_for="xticks_rotation", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["xticks_rotation"],id='xticks_rotation', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Y ticks",style={"margin-top":"5px"}),
                                                style={"textAlign":"left"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("font size",html_for="yticks_fontsize", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["yticks_fontsize"],id='yticks_fontsize', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("rotation",html_for="yticks_rotation", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["yticks_rotation"],id='yticks_rotation', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                        ],
                                        className="g-1",
                                    ),

                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("X limits",style={"margin-top":"5px"}),
                                                style={"textAlign":"left"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("lower",html_for="x_lower_limit",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["x_lower_limit"],id='x_lower_limit', placeholder="", type='text', style=card_input_style),
                                                width = 3
                                            ),
                                            dbc.Col(
                                                dbc.Label("upper",html_for="x_upper_limit", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["x_upper_limit"],id='x_upper_limit', placeholder="", type='text', style=card_input_style),
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Y limits",style={"margin-top":"5px"}),
                                                style={"textAlign":"left"},
                                                width=2
                                            ),
                                            dbc.Col(
                                            dbc.Label("lower",html_for="y_lower_limit", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["y_lower_limit"],id='y_lower_limit', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                            dbc.Label("upper",html_for="y_upper_limit", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["y_upper_limit"],id='y_upper_limit', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("N ticks",style={"margin-top":"5px"}),
                                                style={"textAlign":"left"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("x-axis",html_for="maxxticks",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["maxxticks"],id='maxxticks', placeholder="", type='text', style=card_input_style) ,
                                            ),
                                            dbc.Col(
                                                dbc.Label("y-axis",html_for="maxyticks",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["maxyticks"],id='maxyticks', placeholder="", type='text', style=card_input_style) ,
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
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Spikes"), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Type",html_for="spikes_value", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["spikes"]), value=pa["spikes_value"], placeholder="spikes_value", id='spikes_value', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Color",html_for="spikes_color",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["spikes_color"], placeholder="spikes_color", id='spikes_color', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Mode",html_for="spikes_mode",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["spikes_modes"]), value=pa["spikes_mode"], placeholder="spikes_mode", id='spikes_mode', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Dash",html_for="spikes_dash",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["dashes"]), value=pa["spikes_dash"], placeholder="spikes_dash", id='spikes_dash', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Thickness",html_for="spikes_thickness", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["spikes_thickness"],id='spikes_thickness', placeholder="", type='text', style=card_input_style),
                                                width = 3
                                            ),
                                            dbc.Label("",width=5),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                    ],
                                    className="g-1",
                                    justify="start"),
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Grid"), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Type",html_for="grid_value", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["grid"]), value=pa["grid_value"], placeholder="grid_value", id='grid_value', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("Color",html_for="grid_color", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["grid_color"], placeholder="grid_color", id='grid_color', multi=False, clearable=False, style=card_input_style),
                                                width=5
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Width",html_for="grid_width", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["grid_width"],id='grid_width', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Label("",width=5),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"axes"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
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
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Legend Title", style = {'margin-top': '5px'}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Text",html_for="legend_title", width="auto", style={'margin-top': '0px',"text-align":"right"}),#,"margin-left":"0px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_title"],id='legend_title', placeholder="", type='text', style={"width":"100%"}) ,
                                            ),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Label("Location",html_for="legend_side", width="auto", style={"margin-left":"0px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["sides"]), value=pa["legend_side"], placeholder="legend_side", id='legend_side', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Col(
                                                dbc.Label("X coordinates"),#, style = {'margin-top': '0px'}), #"height":"35px",
                                                # style={"textAlign":"left","padding-right":"2px"},
                                                # width=4
                                            # ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Position",html_for="legend_x",style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_x"],id='legend_x', placeholder="", type='text', style=card_input_style),
                                                width=3
                                            ),
                                            dbc.Col(
                                                dbc.Label("Anchor",html_for="legend_xanchor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["legend_xanchors"]), value=pa["legend_xanchor"], placeholder="legend_xanchor", id='legend_xanchor', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Col(
                                                dbc.Label("Y coordinates", style = {'margin-top': '10px'}), #"height":"35px",
                                                # style={"textAlign":"left","padding-right":"2px"},
                                                # width=4
                                            # ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Position",html_for="legend_y", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_y"],id='legend_y', placeholder="", type='text', style=card_input_style) ,
                                                width = 3
                                            ),
                                            dbc.Col(
                                                dbc.Label("Anchor",html_for="legend_yanchor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["legend_yanchors"]), value=pa["legend_yanchor"], placeholder="legend_yanchor", id='legend_yanchor', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Font", style = {"margin-top": "10px"}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Family",html_for="legend_title_fontfamily", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["legend_title_fontfamily"], placeholder="legend_title_fontfamily", id='legend_title_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                width=9
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Color",html_for="legend_title_fontcolor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_title_fontcolor"], placeholder="legend_title_fontcolor", id='legend_title_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                width=4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Size",html_for="legend_title_fontsize", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["legend_title_fontsize"], placeholder="legend_title_fontsize", id='legend_title_fontsize', multi=False, clearable=False, style=card_input_style),
                                                width=3
                                            )
                                       ],
                                        className="g-1",
                                        justify="start"
                                    ),                                
                                    ############################
                                    dbc.Row([
                                        html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                    ],
                                    className="g-1",
                                    justify="start"),
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Main Body"), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Col(
                                                dbc.Label("Border"),
                                                # style={"textAlign":"left","padding-right":"2px"},
                                                # width=2
                                            # ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Color",html_for="legend_bordercolor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_bordercolor"], placeholder="legend_bordercolor", id='legend_bordercolor', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Width",html_for="legend_borderwidth", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_borderwidth"],id='legend_borderwidth', placeholder="", type='text', style=card_input_style) ,
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Col(
                                            dbc.Label("Trace"),
                                                # style={"textAlign":"left","padding-right":"2px"},
                                                # width=2
                                            # ),

                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Order",html_for="legend_traceorder", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["traceorders"]), value=pa["legend_traceorder"], placeholder="legend_traceorder", id='legend_traceorder', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Group gap",html_for="legend_tracegroupgap", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["legend_tracegroupgap"],id='legend_tracegroupgap', placeholder="", type='text', style=card_input_style) ,
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Orientation",html_for="legend_orientation", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["legend_orientations"]), value=pa["legend_orientation"], placeholder="legend_orientation", id='legend_orientation', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            ),
                                            dbc.Col(
                                                dbc.Label("BKG color",html_for="legend_bgcolor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_bgcolor"], placeholder="legend_bgcolor", id='legend_bgcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            # dbc.Label("",width=2),
                                            dbc.Col(
                                                dbc.Label("Alignment",html_for="legend_valign", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["valignments"]), value=pa["legend_valign"], placeholder="legend_valign", id='legend_valign', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            ),
                                            # dbc.Label("",width=5),
                                        ],
                                        className="g-1",
                                        justify="start"
                                    ),
                                    ############################
                                    dbc.Row(
                                            dbc.Label("Font", style = {"margin-top": "10px"}), #"height":"35px",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Family",html_for="legend_fontfamily", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["legend_fontfamily"], placeholder="legend_fontfamily", id='legend_fontfamily', multi=False, clearable=False, style=card_input_style),
                                                width = 9
                                            ),
                                        ],
                                        className="g-1",
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Color",html_for="legend_fontcolor", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["colors"]), value=pa["legend_fontcolor"], placeholder="legend_fontcolor", id='legend_fontcolor', multi=False, clearable=False, style=card_input_style),
                                                width = 4
                                            ),
                                            dbc.Col(
                                                dbc.Label("Size",html_for="legend_fontsize", style={"margin-top":"5px"}),
                                                style={"textAlign":"right","padding-right":"2px"},
                                                width=2
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["legend_fontsize"], placeholder="legend_fontsize", id='legend_fontsize', multi=False, clearable=False, style=card_input_style),
                                                width = 3
                                            )
                                       ],
                                        className="g-1",
                                    ),                                
                                    ############################

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
                            dcc.Loading(
                                id="loading-fig-output",
                                type="default",
                                children=[
                                    html.Div(id="fig-output", style={"overflow":"scroll"}),
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
                                    dcc.Input(id='pdf-filename', value="dendrogram.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="dendrogram.json", type='text', style={"width":"100%"})
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
        sleep(3)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update

read_input_updates=[
    'fig_width',
    'fig_height',
    'show_legend',
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
    'color_value',
    'color_rgb',
    'orientation',
    'labels',
    'hover_text',
    'dist_func',
    'color_threshold',
    'link_func',
    'xlabel',
    'ylabel',
    'axis_line_color',
    'axis_line_width',
    'label_fontfamily',
    'label_fontcolor',
    'label_fontsize',
    'show_axis',
    'tick_axis',
    'ticks_line_width',
    'ticks_length',
    'ticks_direction_value',
    'ticks_color',
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
    'spikes_color',
    'spikes_mode',
    'spikes_dash',
    'spikes_thickness',
    'grid_value',
    'grid_color',
    'grid_width',
    'legend_title',
    'legend_side',
    'legend_x',
    'legend_xanchor',
    'legend_y',
    'legend_yanchor',
    'legend_title_fontfamily',
    'legend_title_fontcolor',
    'legend_title_fontsize',
    'legend_tracegroupgap',
    'legend_orientation',
    'legend_bgcolor',
    'legend_valign',
    'legend_fontfamily',
    'legend_fontcolor',
    'legend_fontsize',
    'legend_borderwidth',
    'legend_traceorder',
    'legend_bordercolor',
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Output('datacols', 'options'), 
    Output('datacols', 'value'),
    Output('labelcol', 'options'), 
    Output('labelcol', 'value'),
   # Output("json-import",'data'),
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "dendrogram")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            datacols = cols[1:]
            labelcol=cols[0]

            filename=app_data["filename"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"dendrogram")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            datacols = cols[1:]
            labelcol=cols[0]

            # xvals=cols[0]
            # yvals=cols[1]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [ upload_text, None, None, cols_, datacols, cols_, labelcol] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"dendrogram")
        return [dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs

states=[    
    State('datacols', 'value'),
    State('labelcol', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('show_legend', 'value'),
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
    State('color_value', 'value'),
    State('color_rgb', 'value'),
    State('orientation', 'value'),
    State('labels', 'value'),
    State('hover_text', 'value'),
    State('dist_func', 'value'),
    State('color_threshold', 'value'),
    State('link_func', 'value'),
    State('xlabel', 'value'),
    State('ylabel', 'value'),
    State('axis_line_color', 'value'),
    State('axis_line_width', 'value'),
    State('label_fontfamily', 'value'),
    State('label_fontcolor', 'value'),
    State('label_fontsize', 'value'),
    State('show_axis', 'value'),
    State('tick_axis', 'value'),
    State('ticks_line_width', 'value'),
    State('ticks_length', 'value'),
    State('ticks_direction_value', 'value'),
    State('ticks_color', 'value'),
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
    State('spikes_color', 'value'),
    State('spikes_mode', 'value'),
    State('spikes_dash', 'value'),
    State('spikes_thickness', 'value'),
    State('grid_value', 'value'),
    State('grid_color', 'value'),
    State('grid_width', 'value'),
    State('legend_title', 'value'),
    State('legend_side', 'value'),
    State('legend_x', 'value'),
    State('legend_xanchor', 'value'),
    State('legend_y', 'value'),
    State('legend_yanchor', 'value'),
    State('legend_title_fontfamily', 'value'),
    State('legend_title_fontcolor', 'value'),
    State('legend_title_fontsize', 'value'),
    State('legend_tracegroupgap', 'value'),
    State('legend_orientation', 'value'),
    State('legend_bgcolor', 'value'),
    State('legend_valign', 'value'),
    State('legend_fontfamily', 'value'),
    State('legend_fontcolor', 'value'),
    State('legend_fontsize', 'value'),   
    State('legend_borderwidth', 'value'),
    State('legend_traceorder', 'value'),
    State('legend_bordercolor', 'value'),

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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"dendrogram")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_

        session_data={ "session_data": {"app": { "dendrogram": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"dendrogram")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="dendrogram.json"
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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"dendrogram")
            return dash.no_update, toast, None, tb_str, dash.no_update, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    try:
        fig=make_figure(df,pa)
        fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
        fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")

        return fig, None, None, None, download_buttons_style_show, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"dendrogram")
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
        pdf_filename="dendrogram.pdf"
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

    eventlog = UserLogging(email=current_user.email,action="download figure dendrogram")
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

        ask_for_help(tb_str,current_user, "dendrogram", session_data)

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