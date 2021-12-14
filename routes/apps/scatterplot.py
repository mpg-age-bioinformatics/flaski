from myapp import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_table, make_options, make_except_toast, ask_for_help
from pyflaski.scatterplot import make_figure, figure_defaults
import os
import uuid
import traceback
import io
import pandas as pd
import time
import plotly.express as px
from plotly.io import write_image
import plotly.graph_objects as go


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("scatterplot",url_base_pathname='/scatterplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
})

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=False ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-top":"5px"}
card_input_style={"width":"100%","height":"35px"}
card_body_style={ "padding":"2px", "padding-top":"4px"}
# card_body_style={ "padding":"2px", "padding-top":"4px","padding-left":"18px"}


@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    protected_content=html.Div(
        [
            dcc.Store( id='session-data' ),
            make_navbar_logged("Scatter plot",current_user),
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
                            [ 'Drag and Drop or ',html.A('Select File') ], 
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
                            dbc.FormGroup(
                                [
                                    dbc.Label("x values"),
                                    dcc.Dropdown( placeholder="x values", id='xvals', multi=False)
                                ]
                            ),
                            width=4,
                            style={"padding-right":"4px"}
                        ),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("y values" ),
                                    dcc.Dropdown( placeholder="y values", id='yvals', multi=False)
                                ]
                            ),
                            width=4,
                            style={"padding-left":"2px","padding-right":"2px"}
                        ),
                        dbc.Col(
                            dbc.FormGroup(
                                [
                                    dbc.Label("Groups"),
                                    dcc.Dropdown( placeholder="groups", id='groups_value', multi=False)
                                ]
                            ),
                            width=4,
                            style={"padding-left":"4px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    no_gutters=True,
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
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("Width",style={"margin-top":"5px","width":"55px"}),
                                                        dbc.Col(
                                                            dcc.Input(id='fig_width', placeholder="eg. 600", type='text', style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=6,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("Height",style={"margin-top":"5px","width":"55px"}),
                                                        dbc.Col(
                                                            dcc.Input(id='fig_height', placeholder="eg. 600", type='text',style=card_input_style  ) ,
                                                        )
                                                    ],
                                                ),
                                                width=6,
                                                style={ "padding-left":"16px"}
                                            )
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                    ## end of example card body row
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("Title",html_for="title",style={"margin-top":"5px","width":"55px"}),
                                                        dbc.Col(
                                                            dcc.Input(value=pa["title"],id='title', placeholder="title", type='text', style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=8,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("size",html_for="titles",style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["titles"],placeholder="size", id='titles', multi=False, clearable=False),
                                                        )
                                                    ],
                                                ),
                                                width=4,
                                                style={ "padding-left":"16px"}
                                            )
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                    ############################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("Legend",html_for="show_legend",style={"margin-top":"5px","width":"55px"}),
                                                        dbc.Col(
                                                            dcc.Checklist(options=[ {'label':' show legend', 'value':'show_legend'} ], value=pa["show_legend"], id='show_legend', style=card_label_style ),
                                                        )
                                                    ],
                                                ),
                                                width=8,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("size",style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Dropdown(options=make_options(pa["title_size"]), value=pa["legend_font_size"], placeholder="size", id='legend_font_size', multi=False, clearable=False),
                                                        )
                                                    ],
                                                ),
                                                width=4,
                                                style={ "padding-left":"16px"}
                                            )
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
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
                                [
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("x label",html_for='xlabel',style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Input(value=pa["xlabel"],id='xlabel', placeholder="x label", type='text', style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=8,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("size",html_for='xlabels',style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Dropdown( options=make_options(pa["title_size"]), value=pa["xlabels"], placeholder="size", id='xlabels', multi=False, clearable=False, style=card_input_style ),
                                                        )
                                                    ],
                                                ),
                                                width=4,
                                                style={ "padding-left":"16px"}
                                            )
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("y label",html_for='ylabel',style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Input(value=pa["ylabel"] ,id='ylabel', placeholder="y label", type='text', style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=8,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("size",html_for='ylabels',style=card_label_style),
                                                        dbc.Col(
                                                            dcc.Dropdown( options=make_options(pa["title_size"]),value=pa["ylabels"],placeholder="size", id='ylabels', multi=False, clearable=False),
                                                        )
                                                    ],
                                                ),
                                                width=4,
                                                style={ "padding-left":"16px"}
                                            )
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("Axis:",html_for="show_axis",style={"margin-top":"5px","width":"65px"}),
                                            dbc.Col(
                                                dcc.Checklist(
                                                    options=[
                                                        {'label': ' left   ', 'value': 'left_axis'},
                                                        {'label': ' right   ', 'value': 'right_axis'},
                                                        {'label': ' upper   ', 'value': 'upper_axis'},
                                                        {'label': ' lower   ', 'value': 'lower_axis'}
                                                    ],
                                                    value=pa["show_axis"],
                                                    labelStyle={'display': 'inline-block',"margin-right":"10px"},
                                                    style=card_label_style,
                                                    id="show_axis"
                                                ),
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("",style={"margin-top":"5px","width":"65px","margin-right":"4px"}),
                                            dbc.Label("width",style={"margin-top":"5px","margin-right":"4px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["axis_line_width"], id='axis_line_width', placeholder="width", type='text', style=card_input_style ) ,
                                                width=2
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("Ticks:",html_for="tick_axis",style={"margin-top":"5px","width":"65px"}),
                                            dbc.Col(
                                                dcc.Checklist(
                                                    options=[
                                                        {'label': ' X   ', 'value': 'tick_x_axis'},
                                                        {'label': ' Y   ', 'value': 'tick_y_axis'},
                                                    ],
                                                    value=pa["tick_axis"],
                                                    labelStyle={'display': 'inline-block',"margin-right":"13px"},
                                                    style=card_label_style,
                                                    id="tick_axis"
                                                ),
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Label("",style={"margin-top":"5px","width":"65px"}),
                                            dbc.Label("length",style={"margin-top":"5px","margin-right":"4px"}),
                                            dbc.Col(
                                                dcc.Input(value=pa["ticks_length"], id='ticks_length', placeholder="length", type='text', style=card_input_style ) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("direction",style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["ticks_direction"]), value=pa["ticks_direction_value"], id="ticks_direction_value",placeholder="direction", multi=False, clearable=False),
                                                width=3
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("x ticks", style={"margin-top":"5px"}),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("font size", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["xticks_fontsize"], id='xticks_fontsize', placeholder="size", type='text', style=card_input_style ) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("rotation", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["xticks_rotation"], id='xticks_rotation', placeholder="rotation", type='text', style=card_input_style ) ,
                                                width=2
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("y ticks", style=card_label_style),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("font size", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["yticks_fontsize"],id='yticks_fontsize', placeholder="size", type='text', style=card_input_style ) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("rotation", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["yticks_rotation"],id='yticks_rotation', placeholder="rotation", type='text', style=card_input_style ) ,
                                                width=2
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("x limits", style=card_label_style),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("lower", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='x_lower_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("upper", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='x_upper_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                width=2
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("y limits", style=card_label_style),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("lower", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='y_lower_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("upper", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='y_upper_limit', placeholder="value", type='text', style=card_input_style ) ,
                                                width=2
                                            )
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("Grid:", html_for="grid_value",style=card_label_style),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("type", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["grid"]), placeholder="select", id='grid_value', multi=False, style=card_input_style ),
                                                width=2
                                            ),
                                            dbc.Col(
                                                dbc.Label("width", style=card_label_style),
                                                width=3,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Input(value=pa["grid_linewidth"],id='grid_linewidth', placeholder="value", type='text', style=card_input_style ),
                                                width=2,
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("color", style=card_label_style),
                                                width=2,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["grid_colors"]), value=pa["grid_color_value"] ,placeholder="select", id='grid_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='grid_color_text', placeholder=".. or, write color name", type='text', style={"width":"100%","height":"35px"} ),
                                                style={"padding-left":"4px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col([
                                                dbc.Label("hline:", html_for="hline",style={"margin-top":"5px","padding-right":"2px"}),
                                                dcc.Input(id='hline', placeholder="value", type='text', style={"height":"35px","width":"50%"} )],
                                                width=4,
                                            ),
                                            dbc.Col( [
                                                dbc.Label("width", html_for="hline_linewidth", style={"margin-top":"5px","padding-right":"2px"}),
                                                dcc.Input(value=pa["hline_linewidth"],id='hline_linewidth', placeholder="value", type='text', style={"height":"35px","width":"50%"} )],
                                                width=4,
                                            ),
                                            dbc.Label("style", html_for="hline_linestyle_value",style={"margin-top":"5px","padding-right":"2px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["hline_linestyle"]), value=pa["hline_linestyle_value"],placeholder="value", id='hline_linestyle_value', multi=False, clearable=False, style={"height":"35px","width":"100%","margin":"0px"} ),
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("color", style={"margin-top":"5px"}),
                                                width=2,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["hline_colors"]), value=pa["hline_color_value"], placeholder="select", id='hline_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=3
                                            ),

                                            dbc.Col(
                                                dcc.Input(id='hline_color_text', placeholder=".. or, write color name", type='text', style={"width":"100%","height":"35px"} ),
                                                style={"padding-left":"4px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col([
                                                dbc.Label("vline:", html_for="vline",style={"margin-top":"5px","padding-right":"2px"}),
                                                dcc.Input(id='vline', placeholder="value", type='text', style={"height":"35px","width":"50%"} )],
                                                width=4,
                                            ),
                                            dbc.Col( [
                                                dbc.Label("width", html_for="vline_linewidth", style={"margin-top":"5px","padding-right":"2px"}),
                                                dcc.Input(value=pa["vline_linewidth"],id='vline_linewidth', placeholder="value", type='text', style={"height":"35px","width":"50%"} )],
                                                width=4,
                                            ),
                                            dbc.Label("style", html_for="vline_linestyle_value",style={"margin-top":"5px","padding-right":"2px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["vline_linestyle"]), value=pa["vline_linestyle_value"], placeholder="value", id='vline_linestyle_value', multi=False, clearable=False, style={"height":"35px","width":"100%","margin":"0px"} ),
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Label("color", style=card_label_style),
                                                width=2,
                                                style={"textAlign":"right","padding-right":"2px"}
                                            ),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["vline_colors"]), value=pa["vline_color_value"], placeholder="select", id='vline_color_value', multi=False, clearable=False, style=card_input_style ) ,
                                                width=3
                                            ),
                                            dbc.Col(
                                                dcc.Input(id='vline_color_text', placeholder=".. or, write color name", type='text', style={"width":"100%","height":"35px"} ),
                                                style={"padding-left":"4px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                    ),
                                    ############################################ 

                                ],
                                style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"axes"},
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
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("Labels",html_for='labels_col_value',style={"margin-top":"5px","width":"64px"}),
                                                        dbc.Col(
                                                            dcc.Dropdown( placeholder="select a column..", id='labels_col_value', multi=False, style=card_input_style )
                                                            # dcc.Input(id='labels_col_value', placeholder=, type='text', style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=12,
                                                # style={ "padding-right":"16px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("font size",html_for='labels_font_size',style={"margin-top":"5px","width":"64px"}),
                                                        dbc.Col(
                                                            dcc.Dropdown(options=make_options(pa["title_size"]), value=pa["labels_font_size"],id='labels_font_size', placeholder="size", style=card_input_style ) ,
                                                        )
                                                    ],
                                                ),
                                                width=6,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("color",html_for='labels_font_color_value',style={"margin-top":"5px","width":"50px","textAlign":"right"}),
                                                        dbc.Col(
                                                            dcc.Dropdown( options=make_options(pa["labels_font_color"]), value=pa["labels_font_color_value"], placeholder="color", id='labels_font_color_value', multi=False,clearable=False, style=card_input_style )
                                                        )
                                                    ],
                                                ),
                                                width=6,
                                                style={ "padding-left":"16px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    ),
                                ############################################
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("arrows",html_for='labels_arrows_value',style={"margin-top":"5px","width":"64px"}),
                                                        dbc.Col(
                                                            dcc.Dropdown( options=make_options(pa["labels_arrows"]),value=None, placeholder="type", id='labels_arrows_value', multi=False, style=card_input_style )
                                                        )
                                                    ],
                                                ),
                                                width=6,
                                                style={ "padding-right":"16px"}
                                            ),
                                            dbc.Col(
                                                dbc.Row(
                                                    [
                                                        dbc.Label("color",html_for='labels_colors_value',style={"margin-top":"5px","width":"50px","textAlign":"right"}),
                                                        dbc.Col(
                                                            dcc.Dropdown(options=make_options(pa["labels_colors"]), value=pa["labels_colors_value"], placeholder="color", id='labels_colors_value', multi=False, clearable=False,style=card_input_style )
                                                        )
                                                    ],
                                                ),
                                                width=6,

                                                style={ "padding-left":"16px"}
                                            ),
                                        ],
                                        no_gutters=True,
                                        style={ "padding-left":"16px"}
                                    )
                                ############################################                                
                                ]
                                ,style=card_body_style),
                            id={'type':"collapse-dynamic-card","index":"labels"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                )
            ],
            body=True,
            style={"min-width":"372px","width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"4px"}#,'display': 'block'}#,"max-width":"375px","min-width":"375px"}"display":"inline-block"
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
                            style={"width":"100%"}
                        ),
                        dcc.Download(id="saveas-session")
                    ],
                    id="saveas-session-div",
                    width=4,
                    style={"padding-left":"2px"}

                ),
            ],
            style={ "min-width":"372px",},
            # className="g-0",    
            # style={ "margin-left":"0px" , "margin-right":"0px"}
        ),
        dbc.Button(
                    'Submit',
                    id='submit-button-state', 
                    n_clicks=0, 
                    style={"min-width":"372px","width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
                )
    ]

    app_content=html.Div(
        [
            dbc.Row( 
                [
                    dbc.Col(
                        side_bar,
                        sm=12,md=6,lg=5,xl=4,
                        align="top",
                        style={"padding":"2px","overflow":"scroll"},
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
                                                style={"max-width":"150px","width":"100%"}
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

                    #### centered modals need to come here
                    #### https://dash-bootstrap-components.opensource.faculty.ai/docs/components/modal/
                    #### 1x for pdf file name - matching to line 1320 ie. download_pdf()
                    #### 1x for export file name

                ],
            align="start",
            justify="left",
            no_gutters=True,
            style={"height":"87vh","width":"100%"}
            ),
        ]
    )
    return app_content


@dashapp.callback( 
    Output('xvals', 'options'),
    Output('xvals', 'value'),
    Output('yvals', 'options'),
    Output('yvals', 'value'),
    Output('groups_value', 'options'),
    Output('labels_col_value', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename,last_modified,session_id):
    try:
        df=parse_table(contents,filename,last_modified,current_user.id,cache)
        cols=df.columns.tolist()
        cols_=make_options(cols)
        upload_text=html.Div(
            [ html.A(filename) ], 
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )      
        return cols_, cols[0], cols_, cols[1], cols_, cols_, upload_text, None, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"scatterplot")
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, toast, tb_str
   

@dashapp.callback( 
    Output('labels-section', 'children'),
    Output('toast-update_labels_field','children'),
    Output({ "type":"traceback", "index":"update_labels_field" },'data'),
    Input('session-id','data'),
    Input('labels_col_value','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified')
)
def update_labels_field(session_id,col,contents,filename,last_modified):
    try:
        if col:
            df=parse_table(contents,filename,last_modified,current_user.id,cache)
            labels=df[col].tolist()
            labels_=make_options(labels)
            labels_section=dbc.FormGroup(
                [
                    dbc.Col( 
                        dbc.Label("Labels", style={"margin-top":"5px"}),
                        width=2   
                    ),
                    dbc.Col(
                        dcc.Dropdown( options=labels_, value=[],placeholder="labels", id='fixed_labels', multi=True),
                        width=10
                    )
                ],
                row=True
            )
        else:
            labels_section=dbc.FormGroup(
                [
                    dbc.Col( 
                        dbc.Label("Labels", style={"margin-top":"5px"}),
                        width=2   
                    ),
                    dbc.Col(
                        dcc.Dropdown( placeholder="labels", id='fixed_labels', multi=True),
                        width=10
                    )
                ],
                row=True,
                style= {'display': 'none'}
            )

        return labels_section, None, None
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem updating the labels field.","update_labels_field", e, current_user,"scatterplot")
        return dash.no_update, toast, tb_str

@dashapp.callback( 
    Output('marker-cards', 'children'),
    Output('toast-generate_markers','children'),
    Output({ "type":"traceback", "index":"generate_markers" },'data'),
    Input('session-id', 'data'),
    Input('groups_value', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    )
def generate_markers(session_id,groups,contents,filename,last_modified):
    pa=figure_defaults()
    def make_card(card_header,card_id):
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
                        [
                        ############################################
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Label("shape",style={"margin-top":"5px", "width":"45px"}),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["markerstyles"]), value=pa["marker"], placeholder="marker", id={'type':"marker","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                                )
                                            ],
                                        ),
                                        width=8,
                                        style={ "padding-right":"16px"}
                                    ),
                                    dbc.Col(
                                        dbc.Row(
                                            [
                                                dbc.Label("size",style=card_label_style),
                                                dbc.Col(
                                                    dcc.Dropdown( options=make_options(pa["marker_size"]), value=pa["markers"], placeholder="size", id={'type':"markers","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                                )
                                            ],
                                        ),
                                        width=4,
                                        style={ "padding-left":"16px"}
                                    )
                                ],
                                no_gutters=True,
                                style={ "padding-left":"16px"}
                            ),
                       ############################################
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dbc.Label("color",style={"margin-top":"5px", "width":"45px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["marker_color"]), value=pa["markerc"], placeholder="size", id={'type':"markerc","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            )
                                        ],
                                    ),
                                    width=6,
                                ),
                                dbc.Col(
                                        [
                                            dcc.Input(id={'type':"markerc_write","index":str(card_id)}, placeholder=".. or, write color name", type='text', style={"height":"35px","width":"100%"} ),
                                        ],
                                    width=6,
                                )
                            ],
                            no_gutters=True,
                            style={ "padding-left":"16px"}
                        ),
                       ############################################
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dbc.Label("alpha",style={"margin-top":"5px", "width":"45px"}),
                                            dbc.Col(
                                                dcc.Input(id={'type':"marker_alpha","index":str(card_id)}, value=pa["marker_alpha"],placeholder="value", type='text', style={"height":"35px","width":"100%"} ),
                                            )
                                        ],
                                    ),
                                    width=3,
                                ),
                            ],
                            no_gutters=True,
                            style={ "padding-left":"16px"}
                        ),
                       ############################################
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dbc.Label("Line:",style=card_label_style),
                                        ],
                                    ),
                                    width=12,
                                ),
                            ],
                            no_gutters=True,
                            style={ "padding-left":"16px"}
                        ),
                       ############################################
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Row(
                                        [
                                        ],
                                    ),
                                    width=1,
                                ),
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dbc.Label("width",style={"margin-top":"5px", "width":"45px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["edge_linewidths"]), value=pa["edge_linewidth"], placeholder="width", id={'type':"edge_linewidth","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            )
                                        ],
                                    ),
                                    width=5,
                                ),
                            ],
                            no_gutters=True,
                            style={ "padding-left":"16px"}
                        ),
                       ############################################
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Row(
                                        [
                                        ],
                                    ),
                                    width=1,
                                ),
                                dbc.Col(
                                    dbc.Row(
                                        [
                                            dbc.Label("color",style={"margin-top":"5px", "width":"45px"}),
                                            dbc.Col(
                                                dcc.Dropdown( options=make_options(pa["edge_colors"]), value=pa["edgecolor"], placeholder="color", id={'type':"edgecolor","index":str(card_id)}, multi=False, clearable=False, style=card_input_style ),
                                            )
                                        ],
                                    ),
                                    width=5,
                                ),
                                dbc.Col(
                                        [
                                            dcc.Input(id={'type':"edgecolor_write","index":str(card_id)}, placeholder=".. or, write color name", type='text', style={"height":"35px","width":"100%"} ),
                                        ],
                                    width=6,
                                )
                            ],
                            no_gutters=True,
                            style={ "padding-left":"16px"}
                        ),
                       ############################################
                        ],
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
            cards=[ make_card("Marker",0 ) ]
        else:
            cards=[]
            df=parse_table(contents,filename,last_modified,current_user.id,cache)
            groups_=df[[groups]].drop_duplicates()[groups].tolist()
            for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
                card=make_card(g, i)
                cards.append(card)
        return cards, None, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating the marker's card.","generate_markers", e, current_user,"scatterplot")
        return dash.no_update, toast, tb_str


states=[State('xvals', 'value'),
    State('yvals', 'value'),
    State('groups_value', 'value'),
    State('fig_width', 'value'),
    State('fig_height', 'value'),
    State('title', 'value'),
    State('titles', 'value'),
    State('show_legend', 'value'),
    State('legend_font_size', 'value'),
    State('xlabel', 'value'),
    State('xlabels', 'value'),
    State('ylabel', 'value'),
    State('ylabels', 'value'),
    State('show_axis', 'value'),
    State('axis_line_width', 'value'),
    State('tick_axis', 'value'),
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
    State('grid_value', 'value'),
    State('grid_linewidth', 'value'),
    State('grid_color_value', 'value'),
    State('grid_color_text', 'value'),
    State('hline', 'value'),
    State('hline_linewidth', 'value'),
    State('hline_linestyle_value', 'value'),
    State('hline_color_value', 'value'),
    State('hline_color_text', 'value'),
    State('vline', 'value'),
    State('vline_linewidth', 'value'),
    State('vline_linestyle_value', 'value'),
    State('vline_color_value', 'value'),
    State('vline_color_text', 'value'),
    State('labels_col_value', 'value'),
    State('labels_font_size', 'value'),
    State('labels_font_color_value', 'value'),
    State('labels_arrows_value', 'value'),
    State('labels_colors_value', 'value'),
    State('fixed_labels', 'value'),
    State( { 'type': 'marker', 'index': ALL }, "value"),
    State( { 'type': 'markers', 'index': ALL }, "value"),
    State( { 'type': 'markerc', 'index': ALL }, "value"),
    State( { 'type': 'markerc_write', 'index': ALL }, "value"),
    State( { 'type': 'marker_alpha', 'index': ALL }, "value"),
    State( { 'type': 'edge_linewidth', 'index': ALL }, "value"),
    State( { 'type': 'edgecolor', 'index': ALL }, "value"),
    State( { 'type': 'edgecolor_write', 'index': ALL }, "value") ]

@dashapp.callback( 
    Output('fig-output', 'children'),
    Output( 'toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    Output('download-pdf-div', 'style'), 
    Input("submit-button-state", "n_clicks"),
    [ State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,session_id,contents,filename,last_modified,*args):
    download_buttons_style_show={"max-width":"150px","width":"100%","margin":"4px",'display': 'inline-block'} 
    download_buttons_style_hide={"max-width":"150px","width":"100%","margin":"4px",'display': 'none'} 
    try:
        input_names = [item.component_id for item in states]

        df=parse_table(contents,filename,last_modified,current_user.id,cache)

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a

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

        session_data={ "session_data": {"app": { "satterplot": {"filename":filename ,"df":df.to_json(),"pa":pa} } } }

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"scatterplot")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide
    
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

        return fig, None, None, None, download_buttons_style_show

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"scatterplot")
        return dash.no_update, toast, session_data, tb_str, download_buttons_style_hide

@dashapp.callback(
    Output('download-pdf', 'data'),
    Input('download-pdf-btn',"n_clicks"),
    State('graph', 'figure'),
    prevent_initial_call=True
)
def download_pdf(n_clicks,graph):
    def write_image(figure, graph=graph):
        ## This section is for bypassing the mathjax bug on inscription on the final plot
        fig=px.scatter(x=[0, 1, 2, 3, 4], y=[0, 1, 4, 9, 16])        
        fig.write_image(figure, format="pdf")
        time.sleep(2)
        ## 
        fig=go.Figure(graph)
        fig.write_image(figure, format="pdf")
    return dcc.send_bytes(write_image, "some_name.pdf")

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

        ask_for_help(tb_str,current_user, "scatterplot", session_data)

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