from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from flask_login import current_user
from flask_caching import Cache
from flask import abort, send_file
import dash
import os
import uuid
import base64
from io import BytesIO
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from ._kegg import compound_options, pathway_options, organism_options, additional_compound_options, kegg_operations


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("kegg",url_base_pathname=f'{PAGE_PREFIX}/kegg/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="KEGG", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
        dcc.Location( id='url', refresh=False ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-top":"5px"}
card_input_style={"width":"100%","height":"35px"}
card_body_style={ "padding":"2px", "padding-top":"4px"}

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('session-id', 'data')
    )
def make_layout(session_id):

    ## check if user is authorized
    eventlog = UserLogging(email=current_user.email, action="visit kegg")
    db.session.add(eventlog)
    db.session.commit()

    # For better loading
    def make_loading(children,i):
        return dcc.Loading(
            id=f"menu-load-{i}",
            type="default",
            children=children,
        )

    # HTML content from here
    protected_content=html.Div(
        [
            make_navbar_logged("KEGG",current_user),
            html.Div(id="app_access"),
            # html.Div(id="redirect-app"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),

            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [
                                    html.H5("Filters", style={"margin-top":10}), 
                                    html.Label('Compound'), make_loading( dcc.Dropdown( id='opt-compound', multi=True, optionHeight=120), 1),
                                    html.Label('Pathway',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-pathway', optionHeight=90), 2 ),
                                    html.Label('Organism',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-organism'), 3 ),
                                    html.Label('Highlight Additional Compound',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-additional', multi=True, optionHeight=120), 4 ),
                                    html.Label('Download file prefix',style={"margin-top":10}), 
                                    dcc.Input(id='download_name', value="kegg", type='text',style={"width":"100%", "height":"34px"})
                                ],
                                body=True
                            ),
                            dbc.Button(
                                'Submit',
                                id='submit-button-state', 
                                color="secondary",
                                n_clicks=0, 
                                style={"width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
                            )
                        ],
                        xs=12,sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","margin-bottom":"50px"} 
                    ),               
                    dbc.Col(
                        [
                          dcc.Loading(
                              id="loading-output-1",
                              type="default",
                              children=[ html.Div(id="my-output")],
                              style={"margin-top":"50%"} 
                          ),  
                          dcc.Markdown("Based on KEGG (Kyoto Encyclopedia of Genes and Genomes) - https://www.genome.jp/kegg/", style={"margin-top":"15px", "margin-left":"15px"}),
                        ],
                        xs=12,sm=12,md=6,lg=8,xl=9,
                        style={"margin-bottom":"50px"}
                    )
                ],
                align="start",
                justify="left",
                className="g-0",
                style={"width":"100%"}
            ),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

# Callback to load compound list on session load
@dashapp.callback(
    Output(component_id='opt-compound', component_property='options'),
    Input('session-id', 'data')
    )
def update_menus(session_id):
    return compound_options(cache)

# Callback to update opt-pathway based on selected compounds
@dashapp.callback(
    Output('opt-pathway', 'options'),
    Output('opt-pathway', 'placeholder'),
    Input('opt-compound', 'value')
)
def update_pathways(selected_compounds):
    if selected_compounds is None or len(selected_compounds) == 0:
        return [], "No Compound Selected"    
    pw_options=pathway_options(cache, selected_compounds)
    if pw_options is None:
        return [], "No Pathway Found for Selected Compound" 
    return pw_options, "Select Pathway"

# Callback to update opt-organism based on selected pathway
@dashapp.callback(
    Output('opt-organism', 'options'),
    Output('opt-organism', 'placeholder'),
    Input('opt-pathway', 'value')
)
def update_organisms(selected_pathway):
    if selected_pathway is None:
        return [], "No Pathway Selected"    
    org_options=organism_options(cache, selected_pathway)
    if org_options is None:
        return [], "No Organism Found for Selected Pathway" 
    return org_options, "Select Organism"

# Callback to update opt-additional based on selected pathway and organism
@dashapp.callback(
    Output('opt-additional', 'options'),
    Output('opt-additional', 'placeholder'),
    Input('opt-pathway', 'value'),
    Input('opt-organism', 'value')
)
def update_additional(selected_pathway, selected_organism):
    if selected_pathway is None or selected_organism is None:
        return [], "No Available Compound"
    return additional_compound_options(cache, selected_pathway, selected_organism), "Select Additional Compound"


# Callback on submit
@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-compound", "value"),
    State("opt-pathway", "value"),
    State("opt-organism", "value"),
    State("opt-additional", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, compound, pathway, organism, additional_compound, download_name):
    if not n_clicks:
        return html.Div([])
    
    if not compound or pathway is None or organism is None:
        return html.Div([dcc.Markdown("*** Please select at least a compound, pathway and organism!", style={"margin-top":"15px","margin-left":"15px"})])
    
    pdf_buffer, overview, compound_table, gene_table=kegg_operations(cache, compound, pathway, organism, additional_compound)
    if pdf_buffer is None:
        return html.Div([dcc.Markdown("*** Failed to generate network pdf!", style={"margin-top":"15px","margin-left":"15px"})])
    
    pdf_buffer_data=pdf_buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_buffer_data).decode("utf-8")
    pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
    pdf_download_name = f"{download_name}.pdf" if download_name else "kegg.pdf"

    net_pdf_tab=html.Div([
        html.Iframe(src=pdf_data_url, style={"width": "100%", "height": "600px"}),

        html.Div([
            html.A(
                html.Span([
                    html.I(className="fas fa-file-pdf"),
                    " PDF"
                ]),
                id='download-pdf-link',
                href=pdf_data_url,
                download=pdf_download_name,
                className="btn btn-secondary",
                style={"max-width": "150px", "width": "100%", "display": "inline-block", "text-align": "center", "color": "white", "border-radius": "8px"}
            ),
        ], id="download-pdf-div", style={"max-width": "150px", "width": "100%", "margin": "4px"}),

        html.Div([dcc.Markdown("*\* Primaray and additional compounds are highlighted with red and aqua respectively*", style={"margin-top":"10px","margin-left":"15px"})])
    ])

    overview_tab=html.Pre(overview, style={'padding-left': '20px', 'padding-top': '20px'}) 

    output=dcc.Tabs( 
        [ 
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-1",
                    type="default",
                    children=[ net_pdf_tab ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Network PDF", id="tab-net-pdf",
                style={"margin-top":"0%"}
            ),
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-2",
                    type="default",
                    children=[ overview_tab ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Overview", id="tab-overview",
                style={"margin-top":"0%"}
            ),
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-3",
                    type="default",
                    children=[ compound_table ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Compound", id="tab-compound",
                style={"margin-top":"0%"}
            ),
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-4",
                    type="default",
                    children=[ gene_table ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Gene", id="tab-gene",
                style={"margin-top":"0%"}
            )
        ]
    )

    return output

