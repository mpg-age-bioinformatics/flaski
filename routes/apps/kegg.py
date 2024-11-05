from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from flask_login import current_user
from flask_caching import Cache
import dash
import os
import uuid
import base64
import re
from dash import dcc, html, callback_context, no_update
from dash.dependencies import Input, Output, State
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
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), int(os.environ.get('CACHE_REDIS_SENTINELS_port')) ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER'),
        'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD')
    })

# Allow iframe embedding only from the same origin
# @dashapp.server.after_request
# def apply_security_headers(response):
#     response.headers["X-Frame-Options"] = "SAMEORIGIN"
#     response.headers["Content-Security-Policy"] = "frame-ancestors 'self';"
#     return response

# Serve the cached PDF from the server based on session ID and time
# @dashapp.server.route(f"{PAGE_PREFIX}/kegg/serve-cached-pdf/<session_pdf>")
# def serve_cached_pdf(session_pdf):
#     cached_pdf_base64 = cache.get(session_pdf)
#     if not cached_pdf_base64:
#         return "PDF not found or cache timed out, please re-submit!", 404

#     # Decode and convert to BytesIO
#     pdf_data = base64.b64decode(cached_pdf_base64)
#     pdf_buffer = BytesIO(pdf_data)
#     pdf_buffer.seek(0)
#     return send_file(pdf_buffer, mimetype="application/pdf")

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
                                    html.Label('(OR) List of Compound IDs',style={"margin-top":10}),  dcc.Textarea(id='list-compound', placeholder='C00001\nC00002\nC00003', style={'width': '100%', 'height': '100px', 'padding': '10px', 'font-size': '16px'}),
                                    html.Label('Pathway',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-pathway', optionHeight=90), 2 ),
                                    html.Label('Organism',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-organism', optionHeight=60), 3 ),
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
                          dcc.Store(id='stored-compounds'),
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
    Output('stored-compounds', 'data'),
    Input('opt-compound', 'value'),
    Input('list-compound', 'value')
)
def update_pathways(selected_compounds, listed_compounds):
    triggered_input = callback_context.triggered[0]['prop_id'].split('.')[0]

    if triggered_input == 'opt-compound' and selected_compounds:
        if selected_compounds is None or len(selected_compounds) == 0:
            return [], "Invalid Compound Input", []
        pw_options=pathway_options(cache, selected_compounds)
        if pw_options is None:
            return [], "No Pathway Found for Selected Compound", [] 
        return pw_options, "Select Pathway", selected_compounds     
    elif triggered_input == 'list-compound' and listed_compounds:
        if listed_compounds is None or len(listed_compounds) < 6:
            return [], "Invalid Compound Input", []
        lines = listed_compounds.splitlines()
        processed_compounds = [ re.sub(r'\W+', '', line) for line in lines if len(re.sub(r'\W+', '', line)) == 6 ]
        pw_options=pathway_options(cache, processed_compounds)
        if pw_options is None:
            return [], "No Pathway Found for Selected Compound", []
        return pw_options, "Select Pathway", processed_compounds
    else:
       return [], "No Compound Selected", []

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
    Input("stored-compounds", "data"),
    State("opt-pathway", "value"),
    State("opt-organism", "value"),
    State("opt-additional", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, compound, pathway, organism, additional_compound, download_name):
    triggered_input = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_input != 'submit-button-state':
        return no_update
    
    if not n_clicks:
        return html.Div([])
    
    if not compound or pathway is None or organism is None:
        return html.Div([dcc.Markdown("*** Please select at least a compound, pathway and organism!", style={"margin-top":"15px","margin-left":"15px"})])
    
    pdf_buffer, overview, compound_table=kegg_operations(cache, compound, pathway, organism, additional_compound)
    if pdf_buffer is None:
        return html.Div([dcc.Markdown("*** Failed to generate network pdf!", style={"margin-top":"15px","margin-left":"15px"})])
    
    pdf_buffer_data=pdf_buffer.getvalue()
    pdf_base64 = base64.b64encode(pdf_buffer_data).decode("utf-8")
    pdf_data_url = f"data:application/pdf;base64,{pdf_base64}"
    pdf_download_name = f"{download_name}.pdf" if download_name else "kegg.pdf"
    # timestamp_second = int(time.time())
    # cache.set(f"pdf-{session_id}-{timestamp_second}", pdf_base64, timeout=600)

    net_pdf_tab=html.Div([
        html.Iframe(src=pdf_data_url, style={"width": "100%", "height": "550px"}),
        # html.Iframe(src=f"{PAGE_PREFIX}/kegg/serve-cached-pdf/pdf-{session_id}-{timestamp_second}", style={"width": "100%", "height": "600px"}),

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

        html.Div([dcc.Markdown("*\* Primaray and additional compounds are highlighted with red and aqua respectively*", style={"margin-top":"10px","margin-left":"15px"})]),

        html.Div([dcc.Markdown("*\* If fails to display the PDF (due to browser buffer limit), please try a differnt browser (e.g. Firefox, Safari) or download directly with PDF button*", style={"margin-top":"10px","margin-left":"15px"})]),
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
            )
        ]
    )

    return output

