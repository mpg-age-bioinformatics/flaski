from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import make_options, encode_session_app
import os
import uuid
from werkzeug.utils import secure_filename
from time import sleep
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from ._gtex import read_menus,read_genes, get_tables
from pyflaski.violinplot import make_figure

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("gtex",url_base_pathname=f'{PAGE_PREFIX}/gtex/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="GTEx", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    # if "gtex_" in PRIVATE_ROUTES :
    #     appdb=PrivateRoutes.query.filter_by(route="gtex_").first()
    #     if not appdb:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     allowed_users=appdb.users
    #     if not allowed_users:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     if current_user.id not in allowed_users :
    #         allowed_domains=appdb.users_domains
    #         if current_user.domain not in allowed_domains:
    #             return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        # allowed_ips=app.config['WHITELISTED_IPS'].split(',') if app.config['WHITELISTED_IPS'] else []
        # user_ip=request.headers.get('X-Real-IP')
        # if allowed_ips and not any(fnmatch.fnmatch(user_ip, allowed_ip) for allowed_ip in allowed_ips):
        #     return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    ## check if user is authorized
    eventlog = UserLogging(email=current_user.email, action="visit gtex")
    db.session.add(eventlog)
    db.session.commit()

    def make_loading(children,i):
        return dcc.Loading(
            id=f"menu-load-{i}",
            type="default",
            children=children,
        )

    protected_content=html.Div(
        [
            make_navbar_logged("GTEX",current_user),
            html.Div(id="app_access"),
            html.Div(id="redirect-violin"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),
            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [
                                    html.H5("Filters", style={"margin-top":10}), 
                                    html.Label('Gender'), make_loading( dcc.Dropdown( id='opt-genders', multi=True), 1), #opt-datasets
                                    html.Label('Tissue',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-tissues', multi=True), 3 ), #opt-samples
                                    html.Label('Age groups',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-groups', multi=True), 2 ), # opt-groups
                                    html.Label('Gene names',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-genenames', multi=True), 4 ),
                                    html.Label('Gene IDs',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-geneids', multi=True), 5 ),
                                    html.Label('Download file prefix',style={"margin-top":10}), 
                                    dcc.Input(id='download_name', value="gtex", type='text',style={"width":"100%", "height":"34px"})
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
                              id="loading-output-2",
                              type="default",
                              children=[ html.Div(id="my-output")],
                              style={"margin-top":"50%"} 
                          ),
                          dcc.Markdown("Based on GTEx Analysis Release V8 - https://gtexportal.org", style={"margin-top":"15px"})
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

#read_results_files
#read_genes


@dashapp.callback(
    Output(component_id='opt-genders', component_property='options'),
    Output(component_id='opt-tissues', component_property='options'),
    Output(component_id='opt-groups', component_property='options'),
    Output(component_id='opt-genenames', component_property='options'),
    Output(component_id='opt-geneids', component_property='options'),
    Input('session-id', 'data')
    )
def update_menus(session_id):
    menus=read_menus(cache)
    genders=make_options( menus["genders"] )
    tissues=[ s.replace("_._", " - ") for s in menus["tissues"] ]
    tissues=make_options( tissues  )
    groups=make_options( menus["groups"] )

    genes=read_genes(cache)
    genenames=list(set(genes["gene_name"]))
    genenames=make_options(genenames)
    geneids=list(set(genes["gene_id"]))
    geneids=make_options(geneids)

    return genders, tissues, groups, genenames, geneids

@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-genders", "value"),
    State("opt-tissues", "value"),
    State("opt-groups", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, genders, tissues, groups, genenames, geneids, download_name):
    if tissues:
        tissues=[ s.replace(" - ", "_._" ) for s in tissues ]

    swarmplot=[
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col( 
                            [
                                html.Div(
                                    [ 
                                        f"Please select:",\
                                        html.Br(),\
                                        "1 gender",\
                                        html.Br(),\
                                        "1 tissue",\
                                        html.Br(),\
                                        "1 gene name or id",\
                                        html.Br()
                                    ],
                                    style={"textAlign":"center","overflow-wrap": "break-word"}
                                ),
                            ],
                            sm=9,md=7, lg=5, xl=5, 
                            align="top",
                            style={"textAlign":"center", "height": "100%", "margin-top":100  },
                        ),
                        navbar_A,
                    ],
                    justify="center",
                    style={"min-height": "100vh", "margin-bottom":"0px","margin-left":"5px","margin-right":"5px"}
                )
            ]
        )
    ]

    ## if only one gender, one tissue and one gene render a swarm plot of fpkms/tmps (as supplied by gtex)
    ## https://storage.googleapis.com/adult-gtex/bulk-gex/v8/rna-seq/GTEx_Analysis_2017-06-05_v8_RNASeQCv1.1.9_gene_tpm.gct.gz

    data, sigdf, df, pa, session_data = get_tables(cache,genders,tissues,groups,genenames,geneids)

    if pa:
        
        if len(df) > 0 :

            fig=make_figure(df,pa)
            fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
            fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")

            download_bar=html.Div( 
                [   
                    dbc.Button(id='btn-download-values',className="me-1", n_clicks=0, children='Download values', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                    dcc.Download(id="download-values")
                ],
                style={'display': 'inline-block'}
            ) 

            send_to_violinplot=html.Div( 
                [
                    dbc.Button(id='btn-violin-app', n_clicks=0, children='Violin plot', className="me-1",
                    style={"margin-top":4, \
                        "margin-left":4,\
                        "margin-right":4,\
                        'background-color': "#5474d8", \
                        "color":"white",\
                        })
                ],
                style={'display': 'inline-block'}
            )

            message=dcc.Markdown(
                """
                    **Normalized counts**: DESeq2’s median of ratios. Counts divided by sample-specific size factors determined by median ratio \
                    of gene counts relative to geometric mean per gene. Ideal for gene count comparisons between samples and for DE analysis; \
                    NOT for within sample comparisons. Ref.: https://hbctraining.github.io/DGE_workshop_salmon/lessons/02_DGE_count_normalization.html.  
                """ 
            )

            # **Specific tissue information** can be found on the original data. Please consider downloading the values and/or investigating \
            # the SMTSD column once on the violin plot to understand the distribution of the different tissues.

            swarmplot=[fig, message, html.Div( [download_bar, send_to_violinplot]) ]
        
        else:
            
            message=dcc.Markdown(
                """
                    Not enough counts could be found for this gene when subsetting for this gender and tissue.
                """ 
            )

            swarmplot=[ message ]
            


    minwidth=["Data","Significant"]
    minwidth=len(minwidth) * 150
    minwidth = str(minwidth) + "px"

    output=dcc.Tabs( 
        [ 
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-2",
                    type="default",
                    children=[ data ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Data", id="tab-data",
                style={"margin-top":"0%"}
            ),
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-3",
                    type="default",
                    children=[ sigdf ],
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Significant", id="tab-sig",
                style={"margin-top":"0%"}
            ),
            dcc.Tab(
                dcc.Loading(
                    id="loading-output-4",
                    type="default",
                    children=swarmplot,
                    style={"margin-top":"50%","height": "100%"} 
                ), 
                label="Swarmplot", id="tab-swarm",
                style={"margin-top":"0%"}
            )
        ]
    )

    return output


@dashapp.callback(
    Output("download-values", "data"),
    Input("btn-download-values", "n_clicks"),
    State("opt-genders", "value"),
    State("opt-tissues", "value"),
    State("opt-groups", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name','value'),
    prevent_initial_call=True,
)
def download_values(n_clicks,genders, tissues, groups, genenames, geneids, download_name):
    if tissues:
        tissues=[ s.replace(" - ", "_._" ) for s in tissues ]

    data, sigdf, df, pa, session_data =get_tables(cache,genders,tissues,groups,genenames,geneids)

    fileprefix=secure_filename(str(download_name))
    filename="%s.xlsx" %fileprefix
    return dcc.send_data_frame(df.to_excel, filename, sheet_name="gtex", index=False)

@dashapp.callback(
    Output('redirect-violin','children'),
    Input('btn-violin-app', 'n_clicks'),
    State("opt-genders", "value"),
    State("opt-tissues", "value"),
    State("opt-groups", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
)
def to_violin_app(n_clicks, genders, tissues, groups, genenames, geneids):
    if n_clicks:
        if tissues:
            tissues=[ s.replace(" - ", "_._" ) for s in tissues ]

        data, sigdf, df, pa, session_data =get_tables(cache,genders,tissues,groups,genenames,geneids)

        session_data=encode_session_app(session_data)
        session["session_data"]=session_data

        sleep(2)

        return dcc.Location(pathname=f"{PAGE_PREFIX}/violinplot/", id="index")


@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open
