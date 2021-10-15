from myapp import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_table, make_options
from pyflaski.scatterplot import make_figure, figure_defaults
import os
import uuid


dashapp = dash.Dash("scatterplot",url_base_pathname='/scatterplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
})

dashapp.layout=html.Div( 
    [ 
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dcc.Location(id='url', refresh=False),
        html.Div(id="protected-content"),
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
            make_navbar_logged("Scatter plot",current_user),
            html.Div(id="app-content"),
            navbar_A
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
                                dbc.Button( "Figure", color="black", id="figure-card", n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                                            dcc.Input(id='fig_width', placeholder="width", type='text', style=card_input_style ) ,
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
                                                            dcc.Input(id='fig_height', placeholder="height", type='text',style=card_input_style  ) ,
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
                            id="collapse-figure-card",
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Axes", color="black", id="axes-card", n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                            id="collapse-axes-card",
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                ),
                html.Div(id="marker-cards"),
                # dbc.Card(
                #     [
                #         dbc.CardHeader(
                #             html.H2(
                #                 dbc.Button( "Marker", color="black", id="marker-card", n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                #             ),
                #             style={ "height":"40px","padding":"0px"}
                #         ),
                #         dbc.Collapse(
                #             dbc.CardBody("This is the content of group ...",style={ "padding":"6px"}),
                #             id="collapse-marker-card",
                #             is_open=False,
                #         ),
                #     ],
                #     style={"margin-top":"2px","margin-bottom":"2px"} 
                # ),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Labels", color="black", id="labels-card", n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
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
                                                            dcc.Dropdown( options=make_options(pa["labels_arrows"]),value=pa["labels_arrows_value"], placeholder="type", id='labels_arrows_value', multi=False, style=card_input_style )
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
                            id="collapse-labels-card",
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
                )
            ],
            body=True,
            style={"width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"4px"}#,"max-width":"375px","min-width":"375px"}
        ),
        dbc.Button(
                    'Submit',
                    id='submit-button-state', 
                    n_clicks=0, 
                    style={"width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
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
                        style={"padding":"2px"}
                    ),
                    dbc.Col(
                        id="fig-output",
                        sm=12,md=6,lg=7,xl=8,
                        align="top",
                        style={"padding":"2px"}
                    ),
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
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename,last_modified,session_id):
    df=parse_table(contents,filename,last_modified,current_user.id,cache)
    cols=df.columns.tolist()
    cols_=make_options(cols)
    return cols_, cols[0], cols_, cols[1], cols_, cols_

@dashapp.callback( 
    Output('labels-section', 'children'),
    Input('labels_col_value','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def update_labels_field(col,contents,filename,last_modified,session_id):
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
    return labels_section

@dashapp.callback( 
    Output('marker-cards', 'children'),
    Input('session-id', 'data'),
    Input('groups_value', 'value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    )
def generate_markers(session_id,groups,contents,filename,last_modified):
    def make_card(card_header,card_id):
        card=dbc.Card(
            [
                dbc.CardHeader(
                    html.H2(
                        dbc.Button( card_header, color="black", id=f"marker-card-{str(card_id)}", n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                    ),
                    style={ "height":"40px","padding":"0px"}
                ),
                dbc.Collapse(
                    dbc.CardBody("This is the content of group ...",style={ "padding":"6px"}),
                    id=f"collapse-marker-card-{str(card_id)}",
                    is_open=False,
                ),
            ],
            style={"margin-top":"2px","margin-bottom":"2px"} 
        )

        return card

    if not groups:
        cards=[ make_card("Marker",0 ) ]
    else:
        cards=[]
        df=parse_table(contents,filename,last_modified,current_user.id,cache)
        groups_=df[[groups]].drop_duplicates()[groups].tolist()
        for g, i in zip(  groups_, list( range( len(groups_) ) )  ):
            card=make_card(g, i)
            cards.append(card)
    return cards

@dashapp.callback( 
    Output('fig-output', 'children'),
    Input('session-id', 'data'))
def make_fig_output(session_id):
    import plotly.graph_objects as go
    fig = go.Figure( )
    fig.update_layout( )
    fig.add_trace(go.Scatter(x=[1,2,3,4], y=[2,3,4,8]))
    fig.update_layout(
            title={
                'text': "Demo plotly title",
                'xanchor': 'left',
                'yanchor': 'top' ,
                "font": {"size": 25, "color":"black"  } } )
    fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
    fig=dcc.Graph(figure=fig,config=fig_config)
    return fig

@dashapp.callback(
    [Output(f"collapse-{i}", "is_open") for i in  [ "figure-card" ,"axes-card", "marker-card-0", "labels-card" ] ],
    [Input(f"{i}", "n_clicks") for i in [ "figure-card" ,"axes-card", "marker-card-0", "labels-card" ] ],
    [State(f"collapse-{i}", "is_open") for i in [ "figure-card" ,"axes-card", "marker-card-0", "labels-card" ] ],
    prevent_initial_call=True
)
def toggle_accordion(n1, n2, n3, n4, is_open1, is_open2, is_open3, is_open4):

    ctx = dash.callback_context

    cards=[ "figure-card" ,"axes-card", "marker-card-0", "labels-card" ]

    if not ctx.triggered:
        return False, False, False, False
    else:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == cards[0] and n1:
        return not is_open1, False, False, False
    elif button_id == cards[1] and n2:
        return False, not is_open2, False, False
    elif button_id == cards[2] and n3:
        return False, False, not is_open3, False
    elif button_id == cards[3] and n4:
        return False, False, False, not is_open4
    return False, False, False, False


@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open