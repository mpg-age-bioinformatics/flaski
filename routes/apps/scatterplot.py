from myapp import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
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
                html.H5("Arguments", style={"margin-top":10 }),
            ],
            body=True,
            style={"width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"4px"}
        ),
        dbc.Button(
                    'Submit',
                    id='submit-button-state', 
                    n_clicks=0, 
                    style={"width":"100%","margin-top":"2px","margin-bottom":"2px"}
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
    Output('fig-output', 'children'),
    Input('url', 'pathname'))
def make_fig_output(pathname):
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
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open