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
from pyflaski.violinplot import make_figure, figure_defaults
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

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("violinplot",url_base_pathname=f'{PAGE_PREFIX}/violinplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

if app.config["CACHE_TYPE"] == "RedisCache" :
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
        dcc.Location( id='url', refresh=False ),
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
    eventlog = UserLogging(email=current_user.email, action="visit violinplot")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("Violin plot",current_user),
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
                                    dcc.Dropdown( placeholder="x values", id='x_val', multi=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-right":"4px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("y values" ),
                                    dcc.Dropdown( placeholder="y values", id='y_val', multi=False)
                                ],
                            # ),
                            width=4,
                            style={"padding-left":"2px","padding-right":"2px"}
                        ),
                        dbc.Col(
                            # dbc.FormGroup(
                                [
                                    dbc.Label("Groups"),
                                    dcc.Dropdown( placeholder="hue", id='hue', multi=False)
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
                                            # dbc.Col(
                                            dbc.Label("Style",html_for="style", style={"margin-top":"7px","text-align":"right","width":"64px"}),
                                                # width=2,
                                                # style={"textAlign":"right","padding-right":"2px"}
                                            # ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["styles"]), value=pa["style"], placeholder="", id='style', multi=False, clearable=False, style={"height":"35px","width":"100%"}),
                                                # width=10
                                            ),
                                        ],
                                        className="g-1"
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
                html.Div(id="style-cards"),
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
                                                dcc.Dropdown( options=make_options(pa["orientations"]), value=pa["legend_orientation"], placeholder="legend_orientation", id='legend_orientation', multi=False, clearable=False, style=card_input_style),
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
                                [
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("Labels col.",html_for='vp_label',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( placeholder="select a column..", id='vp_label', multi=False, style=card_input_style ),
                                                    width=9
                                                    # dcc.Input(id='labels_col_value', placeholder=, type='text', style=card_input_style ) ,
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        html.Div(id="labels-section"),
                                        ############################################
                                        dbc.Row(
                                            [   
                                                dbc.Label("font size",html_for='fixed_labels_font_size',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["fontsizes"]), value=pa["fixed_labels_font_size"],id='fixed_labels_font_size', placeholder="size", style=card_input_style ) ,
                                                    width=2
                                                ),
                                                dbc.Label("color",html_for='fixed_labels_font_color_value',width=2, style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["colors"]), value=pa["fixed_labels_font_color_value"], placeholder="color", id='fixed_labels_font_color_value', multi=False,clearable=False, style=card_input_style ),
                                                    width=5
                                                )
                                            ],
                                            className="g-1",
                                        ),
                                        ############################################
                                        dbc.Row(
                                            [
                                                dbc.Label("arrows",html_for='fixed_labels_arrows_value',width=3),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["labels_arrows"]),value=None, placeholder="type", id='fixed_labels_arrows_value', multi=False, style=card_input_style ),
                                                    width=2,
                                                ),
                                                dbc.Label("color",html_for='fixed_labels_colors_value',width=2,style={"textAlign":"right"}),
                                                dbc.Col(
                                                    dcc.Dropdown(options=make_options(pa["colors"]), value=pa["fixed_labels_colors_value"], placeholder="color", id='fixed_labels_colors_value', multi=False, clearable=False,style=card_input_style ),
                                                    width=5,
                                                )
                                            ],
                                        className="g-1",
                                        )   
                                        ############################################                                
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"labels"},
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
            dcc.Store( id='generate_styles-import'),
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
                                    html.Div( id="toast-update_labels_field"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"update_labels_field" }), 
                                    html.Div( id="toast-generate_styles" ),
                                    dcc.Store( id={ "type":"traceback", "index":"generate_styles" }), 
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
                                    dcc.Input(id='pdf-filename', value="violinplot.pdf", type='text', style={"width":"100%"})
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
                                    dcc.Input(id='export-filename', value="violinplot.json", type='text', style={"width":"100%"})
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

read_input_updates=[
    'hue',
    'vp_label',
    'fig_width',
    'fig_height',
    'style',
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
    'vp_color_value',
    'vp_color_rgb',
    'vp_scalemode',
    'vp_bw',
    'vp_orient',
    'vp_width',
    'vp_side',
    'vp_span',
    'vp_linecolor',
    'vp_linecolor_rgb',
    'vp_linewidth',
    'vp_meanline_color',
    'vp_meanline_width',
    'vp_mode',
    'vp_gap',
    'vp_groupgap',
    'vp_text',
    'vp_hoveron',
    'vp_hoverinfo',
    'vp_hover_bgcolor',
    'vp_hover_bordercolor',
    'vp_hover_align',
    'vp_hover_fontfamily',
    'vp_hover_fontcolor',
    'vp_hover_fontsize',
    'bp_color_value',
    'bp_color_rgb',
    'bp_orient',
    'bp_width',
    'bp_linecolor',
    'bp_linecolor_rgb',
    'bp_linewidth',
    'bp_boxmean',
    'bp_notched',
    'bp_notchwidth',
    'bp_whiskerwidth',
    'bp_text',
    'bp_hoveron',
    'bp_hoverinfo',
    'bp_hover_bgcolor',
    'bp_hover_bordercolor',
    'bp_hover_align',
    'bp_hover_fontfamily',
    'bp_hover_fontcolor',
    'bp_hover_fontsize',
    'points',
    'marker_fillcolor',
    'marker_color_rgb',
    'marker_opacity',
    'jitter',
    'marker_symbol',
    'marker_size',
    'pointpos',
    'marker_line_color',
    'marker_line_color_rgb',
    'marker_line_width',
    'marker_outliercolor',
    'marker_line_outliercolor',
    'marker_line_outlierwidth',
    'xlabel',
    'ylabel',
    'axis_line_color',
    'axis_line_width',
    'label_fontfamily',
    'label_fontcolor',
    'label_fontsize',
    'fixed_labels_font_size',
    'fixed_labels_font_color_value',
    'fixed_labels_arrows_value',
    'fixed_labels_colors_value',
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
    [Output('x_val', 'options'),
    Output('y_val', 'options'),
    Output('hue', 'options'),
    Output('vp_label', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('x_val', 'value'),
    Output('y_val', 'value')] + read_input_updates_outputs ,
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
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "violinplot")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            x_val=app_data['pa']["x_val"]
            y_val=app_data['pa']["y_val"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"violinplot")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            x_val=cols[0]
            y_val=cols[1]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [ cols_, cols_, cols_, cols_, upload_text, None, None,  x_val, y_val] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"violinplot")
        return [ dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs


@dashapp.callback( 
    Output('labels-section', 'children'),
    Output('toast-update_labels_field','children'),
    Output({ "type":"traceback", "index":"update_labels_field" },'data'),
    Output('update_labels_field-import', 'data'),
    Input('session-id','data'),
    Input('vp_label','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('update_labels_field-import', 'data'),
)
def update_labels_field(session_id,col,contents,filename,last_modified,update_labels_field_import):
    try:
        if col:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"violinplot")
            labels=df[[col]].drop_duplicates()[col].tolist()
            labels_=make_options(labels)

            if ( filename.split(".")[-1] == "json" ) and ( not update_labels_field_import ) :
                app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "violinplot")
                fixed_labels=app_data['pa']["fixed_labels"]
                update_labels_field_import=True
            else:
                fixed_labels=[]


            labels_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Labels", width=3),
                        dbc.Col(
                            dcc.Dropdown( options=labels_, value=fixed_labels,placeholder="labels", id='fixed_labels', multi=True),
                            width=9
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
                        dbc.Label("Labels", width=3),
                        dbc.Col(
                            dcc.Dropdown( placeholder="labels", id='fixed_labels', multi=True),
                            width=9
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
        toast=make_except_toast("There was a problem updating the labels field.","update_labels_field", e, current_user,"violinplot")
        return dash.no_update, toast, tb_str, dash.no_update


@dashapp.callback( 
    Output('style-cards', 'children'),
    Output('toast-generate_styles','children'),
    Output({ "type":"traceback", "index":"generate_styles" },'data'),
    Output('generate_styles-import', 'data'),
    Input('session-id', 'data'),
    Input('style', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('generate_styles-import', 'data'),
    )
def generate_styles(session_id,styles,contents,filename,last_modified,generate_styles_import):
    pa=figure_defaults()
    if filename :
        if ( filename.split(".")[-1] == "json") and ( not generate_styles_import ):
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "violinplot")
            pa=app_data['pa']
            generate_styles_import=True

    def make_card(card_header,pa, selected_styles):
        if card_header == "Violinplot":
            if card_header in selected_styles:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"inline-block"}
                card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 
            else:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"none"}
                card_style_on_off={"margin-top":"0px","margin-bottom":"0px", 'display':"none" } 
                # card_style_on_off="none"
            # card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 

            card=dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(
                            dbc.Button( "Violin Plot", color="black", id={'type':"dynamic-card","index":"violinplot"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                        ),
                        style={ "height":"40px","padding":"0px"}
                        # style=card_style_on_off
                    ),
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                           dbc.Label("Color",html_for="vp_color_value", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_color_value"], placeholder="vp_color_value", id='vp_color_value', multi=False, clearable=False, style=card_input_style),
                                            width = 4
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="vp_color_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=2
                                        # ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_color_rgb"],id='vp_color_rgb', placeholder="or write", type='text', style=card_input_style),
                                            width = 5
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Scale",html_for="vp_scalemode", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["scalemodes"]), value=pa["vp_scalemode"], placeholder="vp_scalemode", id='vp_scalemode', multi=False, clearable=False, style=card_input_style),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Label("Bandwidth",html_for="vp_bw", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                    dbc.Col(
                                            dcc.Input(value=pa["vp_bw"],id='vp_bw', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Orientation",html_for="vp_orient", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["orientations"]), value=pa["vp_orient"], placeholder="vp_orient", id='vp_orient', multi=False, clearable=False, style=card_input_style),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Label("Violin Width",html_for="vp_width", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_width"],id='vp_width', placeholder="", type='text', style=card_input_style),
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Side",html_for="vp_side", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["vp_sides"]), value=pa["vp_side"], placeholder="vp_side", id='vp_side', multi=False, clearable=False, style=card_input_style),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Label("Span",html_for="vp_span", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["spans"]), value=pa["vp_span"], placeholder="vp_span", id='vp_span', multi=False, clearable=False, style=card_input_style),
                                            width=3
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
                                        dbc.Label("Border"), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Color",html_for="vp_linecolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_linecolor"], placeholder="vp_linecolor", id='vp_linecolor', multi=False, clearable=False, style=card_input_style),
                                            width=5
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="vp_linecolor_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=3
                                        #     ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_linecolor_rgb"],id='vp_linecolor_rgb', placeholder="or write", type='text', style=card_input_style),
                                            width=5
                                        ),

                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=7),
                                        dbc.Col(
                                            dbc.Label("Width",html_for="vp_linewidth", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_linewidth"],id='vp_linewidth', placeholder="vp_linewidth", type='text', style=card_input_style),
                                            width=3
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row(
                                        dbc.Label("Meanline", style={"margin-top":"10px"}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                        dbc.Label("Color",html_for="vp_meanline_color", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_meanline_color"], placeholder="vp_meanline_color", id='vp_meanline_color', multi=False, clearable=False, style=card_input_style),
                                            width=5
                                        ),
                                        dbc.Col(
                                        dbc.Label("Width",html_for="vp_meanline_width", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_meanline_width"],id='vp_meanline_width', placeholder="", type='text', style=card_input_style),
                                            width=3
                                        )
                                    ],
                                    className="g-1"
                                ),                                
                                ############################
                                dbc.Row(
                                        dbc.Label("Layout", style={"margin-top":"10px"}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Mode",html_for="vp_mode", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["violinmodes"]), value=pa["vp_mode"], placeholder="vp_mode", id='vp_mode', multi=False, clearable=False, style=card_input_style),
                                            width=5
                                        ),
                                        dbc.Col(
                                            dbc.Label("Gap",html_for="vp_gap", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_gap"],id='vp_gap', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=6),
                                        dbc.Col(
                                            dbc.Label("Groupgap",html_for="vp_groupgap", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_groupgap"],id='vp_groupgap', placeholder="vp_groupgap", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                ],
                                className="g-1",
                                justify="start"),
                                ############################
                                dbc.Row(
                                        dbc.Label("Hover"), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Text",html_for="vp_text", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["vp_text"],id='vp_text', placeholder="", type='text', style=card_input_style) ,
                                            width=9
                                        )
                                    ],
                                    className="g-1",
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Hover on",html_for="vp_hoveron", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["vp_hoverons"]), value=pa["vp_hoveron"], placeholder="vp_hoveron", id='vp_hoveron', multi=False, clearable=False, style=card_input_style),
                                            width=9
                                        ),
                                    ],
                                    className="g-1",
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Hover Info",html_for="vp_hoverinfo", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hoverinfos"]), value=pa["vp_hoverinfo"], placeholder="vp_hoverinfo", id='vp_hoverinfo', multi=False, clearable=False, style=card_input_style),
                                            width=9
                                        )
                                    ],
                                    className="g-1",
                                ),                                
                                ############################
                                dbc.Row(
                                        dbc.Label("Color", style = {"margin-top": "10px"}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("BKG",html_for="vp_hover_bgcolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_hover_bgcolor"], placeholder="vp_hover_bgcolor", id='vp_hover_bgcolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("Border",html_for="vp_hover_bordercolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_hover_bordercolor"], placeholder="vp_hover_bordercolor", id='vp_hover_bordercolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=5),
                                        dbc.Col(
                                            dbc.Label("Alignment",html_for="vp_hover_align", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hover_alignments"]), value=pa["vp_hover_align"], placeholder="vp_hover_align", id='vp_hover_align', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
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
                                        dbc.Label("Family",html_for="vp_hover_fontfamily", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["vp_hover_fontfamily"], placeholder="vp_hover_fontfamily", id='vp_hover_fontfamily', multi=False, clearable=False, style=card_input_style),
                                            width=10
                                        ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Color",html_for="vp_hover_fontcolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["vp_hover_fontcolor"], placeholder="vp_hover_fontcolor", id='vp_hover_fontcolor', multi=False, clearable=False, style=card_input_style),
                                            width=5
                                        ),
                                        dbc.Col(
                                        dbc.Label("Size",html_for="vp_hover_fontsize", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["vp_hover_fontsize"], placeholder="vp_hover_fontsize", id='vp_hover_fontsize', multi=False, clearable=False, style=card_input_style),
                                            width=2
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                            ######### END OF CARD #########
                            ]
                            ,style=card_body_style
                        ),
                        id={'type':"collapse-dynamic-card","index":"violinplot"},
                        is_open=False,
                    ),
                ],
                style=card_style_on_off#{"margin-top":"2px","margin-bottom":"2px",'display':card_style_on_off} 
            )
        elif card_header == "Boxplot":
            if card_header in selected_styles:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"inline-block"}
                card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 
            else:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"none"}
                card_style_on_off={"margin-top":"0px","margin-bottom":"0px", 'display':"none" } 
                # card_style_on_off="none"
            # card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 

            card = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(
                            dbc.Button( "Box Plot", color="black", id={'type':"dynamic-card","index":"boxplot"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                        ),
                        style={ "height":"40px","padding":"0px"}
                        # style=card_style_on_off
                    ),
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Fill color",html_for="bp_color_value", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["bp_color_value"], placeholder="bp_color_value", id='bp_color_value', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="bp_color_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=3
                                        #     ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_color_rgb"],id='bp_color_rgb', placeholder="or write", type='text', style=card_input_style) ,
                                            width=5
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Orientation",html_for="bp_orient", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["orientations"]), value=pa["bp_orient"], placeholder="bp_orient", id='bp_orient', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("Box Width",html_for="bp_width", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_width"],id='bp_width', placeholder="", type='text', style=card_input_style) ,
                                            width=2
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row(
                                        dbc.Label("Boxline"), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Color",html_for="bp_linecolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["bp_linecolor"], placeholder="bp_linecolor", id='bp_linecolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="bp_linecolor_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=3
                                        #     ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_linecolor_rgb"],id='bp_linecolor_rgb', placeholder="or write", type='text', style=card_input_style) ,
                                            width=5
                                        ),
                                    ],
                                    className="g-1"
                                ),        
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Boxmean",html_for="bp_boxmean", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["boxmeans"]), value=pa["bp_boxmean"], placeholder="bp_boxmean", id='bp_boxmean', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("Width",html_for="bp_linewidth", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_linewidth"],id='bp_linewidth', placeholder="bp_linewidth", type='text', style=card_input_style) ,
                                            width=2
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Draw notch",html_for="bp_notched"),
                                            style={"textAlign":"right","padding-right":"2px", "magin-top":"5px"},
                                            width=4
                                            ),
                                        dbc.Col(
                                            dcc.Checklist(options=[ {'value':'bp_notched'} ], value=pa["bp_notched"], id='bp_notched', style={"height":"35px"} ),
                                            width=2
                                            # className="me-3",
                                            # width=5
                                        ),
                                        dbc.Col(
                                            dbc.Label("Notch width", html_for="bp_notchwidth", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=4
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_notchwidth"],id='bp_notchwidth', placeholder="bp_notchwidth", type='text', style=card_input_style) ,
                                            width=2
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=6),
                                        dbc.Col(
                                            dbc.Label("Whisker width",html_for="bp_whiskerwidth", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=4
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_whiskerwidth"],id='bp_whiskerwidth', placeholder="bp_whiskerwidth", type='text', style=card_input_style) ,
                                            width=2
                                        ),
                                    ],
                                    className="g-1"
                                ),
                                ############################
                                dbc.Row([
                                    html.Hr(style={'width' : "100%", "height" :'2px', "margin-top":"15px" })
                                ],
                                className="g-1",
                                justify="start"),
                                ############################
                                dbc.Row(
                                        dbc.Label("Hover"), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Text",html_for="bp_text", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["bp_text"],id='bp_text', placeholder="", type='text', style=card_input_style),
                                            width=9
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Hover on",html_for="bp_hoveron", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["bp_hoverons"]), value=pa["bp_hoveron"], placeholder="bp_hoveron", id='bp_hoveron', multi=False, clearable=False, style=card_input_style),
                                            width=9
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Hover Info",html_for="bp_hoverinfo", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hoverinfos"]), value=pa["bp_hoverinfo"], placeholder="bp_hoverinfo", id='bp_hoverinfo', multi=False, clearable=False, style=card_input_style),
                                            width=9
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                        dbc.Label("Color", style = {"margin-top": "10px"}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("BKG",html_for="bp_hover_bgcolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["bp_hover_bgcolor"], placeholder="bp_hover_bgcolor", id='bp_hover_bgcolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("Border",html_for="bp_hover_bordercolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["bp_hover_bordercolor"], placeholder="bp_hover_bordercolor", id='bp_hover_bordercolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("",width=5),
                                        dbc.Col(
                                            dbc.Label("Alignment",html_for="bp_hover_align", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["hover_alignments"]), value=pa["bp_hover_align"], placeholder="bp_hover_align", id='bp_hover_align', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
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
                                        dbc.Label("Family",html_for="bp_hover_fontfamily", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fonts"]), value=pa["bp_hover_fontfamily"], placeholder="bp_hover_fontfamily", id='bp_hover_fontfamily', multi=False, clearable=False, style=card_input_style),
                                            width=10
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                        dbc.Label("Color",html_for="bp_hover_fontcolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["bp_hover_fontcolor"], placeholder="bp_hover_fontcolor", id='bp_hover_fontcolor', multi=False, clearable=False, style=card_input_style),
                                            width=5
                                        ),
                                        dbc.Col(
                                        dbc.Label("Size",html_for="bp_hover_fontsize", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["fontsizes"]), value=pa["bp_hover_fontsize"], placeholder="bp_hover_fontsize", id='bp_hover_fontsize', multi=False, clearable=False, style=card_input_style),
                                            width=2
                                        )
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),                                
                            ######### END OF CARD #########
                            ]
                            ,style=card_body_style
                        ),
                        id={'type':"collapse-dynamic-card","index":"boxplot"},
                        is_open=False,
                    ),
                ],
                style=card_style_on_off#{"margin-top":"2px","margin-bottom":"2px",'display':card_style_on_off} 
            )
        elif card_header == "Swarmplot":
            if card_header in selected_styles:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"inline-block"}
                card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 
            else:
                # card_style_on_off={ "height":"40px","padding":"0px", 'display':"none"}
                card_style_on_off={"margin-top":"0px","margin-bottom":"0px", 'display':"none" } 
                # card_style_on_off="none"
            # card_style_on_off={"margin-top":"2px","margin-bottom":"2px"}#, 'display':"inline-block" } 

            card = dbc.Card(
                [
                    dbc.CardHeader(
                        html.H2(
                            dbc.Button( "Swarm Plot", color="black", id={'type':"dynamic-card","index":"swarmplot"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                        ),
                        style={ "height":"40px","padding":"0px"}
                        # style=card_style_on_off
                    ),
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                        dbc.Label("Display",html_for="points", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["display_points"]), value=pa["points"], placeholder="points", id='points', multi=False, clearable=False, style=card_input_style),
                                            width=9
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                        dbc.Label("Points", style = {'margin-top': '10px'}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Fill color",html_for="marker_fillcolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["marker_fillcolor"], placeholder="marker_fillcolor", id='marker_fillcolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="marker_color_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=3
                                        #     ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_color_rgb"],id='marker_color_rgb', placeholder="or write", type='text', style=card_input_style) ,
                                            width=5
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Opacity",html_for="marker_opacity", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_opacity"],id='marker_opacity', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Label("Jitter",html_for="jitter", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["jitter"],id='jitter', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Symbol",html_for="marker_symbol", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["marker_symbols"]), value=pa["marker_symbol"], placeholder="marker_symbol", id='marker_symbol', multi=False, clearable=False, style=card_input_style),
                                            width=3
                                        ),
                                        dbc.Col(
                                            dbc.Label("Size",html_for="marker_size", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_size"],id='marker_size', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("", width = 6),
                                        dbc.Col(
                                            dbc.Label("Position",html_for="pointpos", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["pointpos"],id='pointpos', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                        dbc.Label("Outerline", style = {'margin-top': '10px'}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Color",html_for="marker_line_color", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["marker_line_color"], placeholder="marker_line_color", id='marker_line_color', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        # dbc.Col(
                                        #     dbc.Label("or write",html_for="marker_line_color_rgb", style={"margin-top":"5px"}),
                                        #     style={"textAlign":"right","padding-right":"2px"},
                                        #     width=3
                                        #     ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_line_color_rgb"],id='marker_line_color_rgb', placeholder="or write", type='text', style=card_input_style) ,
                                            width=5
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("", width = 6),
                                        dbc.Col(
                                            dbc.Label("Width",html_for="marker_line_width", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_line_width"],id='marker_line_width', placeholder="", type='text', style=card_input_style) ,
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                        dbc.Label("Outlier", style = {'margin-top': '10px'}), #"height":"35px",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Label("Fill",html_for="marker_outliercolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["marker_outliercolor"], placeholder="marker_outliercolor", id='marker_outliercolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                        dbc.Col(
                                            dbc.Label("Line",html_for="marker_line_outliercolor", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=2
                                            ),
                                        dbc.Col(
                                            dcc.Dropdown( options=make_options(pa["colors"]), value=pa["marker_line_outliercolor"], placeholder="marker_line_outliercolor", id='marker_line_outliercolor', multi=False, clearable=False, style=card_input_style),
                                            width=4
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                                dbc.Row(
                                    [
                                        dbc.Label("", width = 6),
                                        dbc.Col(
                                            dbc.Label("Width",html_for="marker_line_outlierwidth", style={"margin-top":"5px"}),
                                            style={"textAlign":"right","padding-right":"2px"},
                                            width=3
                                            ),
                                        dbc.Col(
                                            dcc.Input(value=pa["marker_line_outlierwidth"],id='marker_line_outlierwidth', placeholder="", type='text', style=card_input_style),
                                            width=3
                                        ),
                                    ],
                                    className="g-1",
                                    justify="start"
                                ),
                                ############################
                        
                            ######### END OF CARD #########
                            ]
                            ,style=card_body_style
                        ),
                        id={'type':"collapse-dynamic-card","index":"swarmplot"},
                        is_open=False,
                    ),
                ],
                style=card_style_on_off#{"margin-top":"2px","margin-bottom":"2px", 'display':"None" } 
            )
        return card

    try:

        cards=[]
        selected_styles=styles.split(" and ")
        styles_=["Violinplot", "Boxplot", "Swarmplot"]
        for g in styles_:
                card=make_card(g, pa, selected_styles)
                cards.append(card)
        return cards, None, None, generate_styles_import

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the styles's card.","generate_styles", e, current_user,"violinplot")
        return dash.no_update, toast, tb_str, dash.no_update


states=[State('x_val', 'value'),
    State('y_val', 'value'),
    State('hue', 'value'),
    State('vp_label', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('style', 'value'),
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
    State('vp_color_value', 'value'),
    State('vp_color_rgb', 'value'),
    State('vp_scalemode', 'value'),
    State('vp_bw', 'value'),
    State('vp_orient', 'value'),
    State('vp_width', 'value'),
    State('vp_side', 'value'),
    State('vp_span', 'value'),
    State('vp_color_value', 'value'),
    State('vp_color_rgb', 'value'),
    State('vp_scalemode', 'value'),
    State('vp_bw', 'value'),
    State('vp_orient', 'value'),
    State('vp_width', 'value'),
    State('vp_side', 'value'),
    State('vp_linecolor', 'value'), 
    State('vp_linecolor_rgb', 'value'), 
    State('vp_linewidth', 'value'), 
    State('vp_meanline_color', 'value'), 
    State('vp_meanline_width', 'value'), 
    State('vp_mode', 'value'), 
    State('vp_gap', 'value'), 
    State('vp_groupgap', 'value'), 
    State('vp_text', 'value'), 
    State('vp_hoveron', 'value'), 
    State('vp_hoverinfo', 'value'), 
    State('vp_hover_bgcolor', 'value'), 
    State('vp_hover_bordercolor', 'value'), 
    State('vp_hover_align', 'value'), 
    State('vp_hover_fontfamily', 'value'), 
    State('vp_hover_fontcolor', 'value'), 
    State('vp_hover_fontsize', 'value'),
    State('bp_color_value', 'value'), 
    State('bp_color_rgb', 'value'), 
    State('bp_orient', 'value'), 
    State('bp_width', 'value'), 
    State('bp_linecolor', 'value'), 
    State('bp_linecolor_rgb', 'value'), 
    State('bp_linewidth', 'value'), 
    State('bp_boxmean', 'value'), 
    State('bp_notched', 'value'), 
    State('bp_notchwidth', 'value'), 
    State('bp_whiskerwidth', 'value'), 
    State('bp_text', 'value'), 
    State('bp_hoveron', 'value'), 
    State('bp_hoverinfo', 'value'), 
    State('bp_hover_bgcolor', 'value'), 
    State('bp_hover_bordercolor', 'value'), 
    State('bp_hover_align', 'value'), 
    State('bp_hover_fontfamily', 'value'), 
    State('bp_hover_fontcolor', 'value'), 
    State('bp_hover_fontsize', 'value'),
    State('points', 'value'), 
    State('marker_fillcolor', 'value'), 
    State('marker_color_rgb', 'value'), 
    State('marker_opacity', 'value'), 
    State('jitter', 'value'), 
    State('marker_symbol', 'value'), 
    State('marker_size', 'value'), 
    State('pointpos', 'value'), 
    State('marker_line_color', 'value'), 
    State('marker_line_color_rgb', 'value'), 
    State('marker_line_width', 'value'), 
    State('marker_outliercolor', 'value'), 
    State('marker_line_outliercolor', 'value'),
    State('marker_line_outlierwidth', 'value'),
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
    State('fixed_labels', 'value'),
    State('fixed_labels_font_size', 'value'),
    State('fixed_labels_font_color_value', 'value'),
    State('fixed_labels_arrows_value', 'value'),
    State('fixed_labels_colors_value', 'value'),
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
    [State('session-id', 'data'),
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

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"violinplot")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
        
        # list of column names
        pa['vals'] = [None] + df.columns.tolist()

        if pa["hue"]:
            groups=df[[ pa["hue"] ]].drop_duplicates()[ pa["hue"] ].tolist()
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

        session_data={ "session_data": {"app": { "violinplot": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.to_json(),"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"violinplot")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, None

    # button_id,  submit-button-state, export-filename-download

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="violinplot.json"
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
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"violinplot")
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
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"violinplot")
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
        pdf_filename="violinplot.pdf"
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
    eventlog = UserLogging(email=current_user.email,action="download figure violinplot")
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

        ask_for_help(tb_str,current_user, "violinplot", session_data)

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