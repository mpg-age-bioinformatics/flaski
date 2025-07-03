from datetime import datetime
from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, make_table, encode_session_app
import os
import uuid
import pandas as pd
from time import sleep
# from plotly.io import write_image
from werkzeug.utils import secure_filename
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from pyflaski.violinplot import figure_defaults
from ._aadatalake_prot import read_meta_file, filter_samples, filter_genes, filter_gene_expression, nFormat, \
    make_pca_plot, make_bar_plot, make_violin_plot, plot_height, read_genes

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("aadatalake_prot",url_base_pathname=f'{PAGE_PREFIX}/aadatalake_prot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="Datalake for Proteomics" , assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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

def change_table_minWidth(tb,minwidth):
    st=tb.style_table
    st["minWidth"]=minwidth
    tb.style_table=st
    return tb

def change_fig_minWidth(fig,minwidth):
    st=fig.style
    st["minWidth"]=minwidth
    fig.style=st
    return fig


dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=False),
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
    Input('session-id', 'data'))
def make_layout(pathname):
    # Check if user is authorized
    if "aadatalake_prot" in PRIVATE_ROUTES :
        appdb=PrivateRoutes.query.filter_by(route="aadatalake_prot").first()
        if not appdb:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        allowed_users=appdb.users
        if not allowed_users:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        if current_user.id not in allowed_users :
            allowed_domains=appdb.users_domains
            if current_user.domain not in allowed_domains:
                return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    # Log stat
    eventlog = UserLogging(email=current_user.email, action="visit aadatlake_prot")
    db.session.add(eventlog)
    db.session.commit()

    def make_loading(children,i):
        return dcc.Loading(id=f"menu-load-{i}", type="default", children=children)

    protected_content=html.Div(
        [
            make_navbar_logged("Datalake for Proteomics",current_user),
            html.Div(id="app_access"),
            html.Div(id="redirect-pca"),
            html.Div(id="redirect-violin"),
            # html.Div(id="redirect-volcano"),
            # html.Div(id="redirect-ma"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),
            dcc.Store(id="pca-data-store"),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card( 
                                [   
                                    html.H5("Filters", style={"margin-top":10}),
                                    html.Label('Data sets'), make_loading( dcc.Dropdown( id='opt-datasets', multi=True), 1),
                                    html.Label('Genotypes',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-genotypes', multi=True), 2 ),
                                    html.Label('Conditions',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-conditions', multi=True), 4 ),
                                    html.Label('WormbaseID',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-geneids', multi=True), 5 ),
                                    html.Label('Download file prefix', style={"margin-top":10}),
                                    dcc.Input(id='download_name', value="data.lake.prot", type='text',style={"width":"100%",  "height":"34px"}),
                                ],
                                body=True
                            ),
                            dbc.Button(
                                'Submit',
                                id='submit-button-state',
                                color="secondary",
                                n_clicks=0,
                                style={"width":"100%","margin-top":"2px","margin-bottom":"2px"}
                            ),
                        ],
                        xs=12,sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","margin-bottom":"50px"}
                    ),
                    dbc.Col(
                        dcc.Loading(
                            id="loading-output-2",
                            type="default",
                            children=[ html.Div(id="my-output")],
                            style={"margin-top":"50%"}
                        ),
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



@dashapp.callback( 
    Output('my-output', 'children'),
    Output('pca-data-store', 'data'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-datasets", "value"),
    State("opt-genotypes", "value"),
    State("opt-conditions", "value"),
    State("opt-geneids", "value"),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, datasets, genotype, condition, geneids, download_name):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,genotype=genotype, condition=condition, cache=cache)    

    ## samples
    results_files=selected_results_files[["study","genotype","condition","time", "PseudoAge"]]
    results_files.columns=["study","genotype","condition","time", "PseudoAge"]
    results_files=results_files.drop_duplicates()
    results_files_=make_table(results_files,"results_files")
    download_samples=html.Div(
        [
            html.Button(id='btn-samples', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-samples")
        ]
    )

    ## gene expression
    if datasets or genotype or condition or geneids :
        # print("1 -- gene expression")
        gene_expression=filter_gene_expression(ids2labels,geneids,cache)

        gene_expression_ = gene_expression.copy()
        gene_expression_['gene_id'] = gene_expression.index
        cols = gene_expression_.columns.tolist()
        gene_expression_ = gene_expression_[[cols[-1]] + cols[:-1]]
        gene_expression_=make_table(gene_expression_,"gene_expression")#,fixed_columns={'headers': True, 'data': 2} )
        download_geneexp=html.Div( 
            [
                html.Button(id='btn-geneexp', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                dcc.Download(id="download-geneexp")
            ]
        )
        gene_expression_bol=True
    else:
        gene_expression_bol=False

    ## barPlot
    selected_sets=list(set(results_files["study"]))

    if geneids :
        lgeneids=len(geneids)
    else:
        lgeneids=0   

    if (geneids and lgeneids == 1):

        gene_expression=filter_gene_expression(ids2labels,geneids,cache)
        
        bar_df=gene_expression
        if geneids:
            label=geneids[0]

        plot_height_=plot_height(selected_sets)
        
        bar_plot=make_bar_plot(bar_df, selected_results_files['study'], selected_results_files['condition'], label)
        bar_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".bar" }}
        bar_plot=dcc.Graph(figure=bar_plot, config=bar_config, style={"width":"100%","overflow-x":"auto", "height":plot_height_}, id="bar_plot")
 
        download_bar=html.Div( 
        [   
            html.Button(id='btn-download-bar', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-bar")
        ])      
        gene_expression_bar_bol=True
    else:
        gene_expression_bar_bol=False


    ## PCA
    selected_study = list(set(selected_results_files["study"]))
    selected_genotype = list(set(selected_results_files["genotype"]))
    selected_condition = list(set(selected_results_files["condition"]))
    pca_store = dash.no_update
    if lgeneids==0 and (len(selected_sets) > 0 or len(selected_condition)): 
        pca_plot, pca_pa, pca_df=make_pca_plot(selected_study, selected_genotype, selected_condition, cache)

        pca_store = {
            "df": pca_df.to_json(),
            "pa": pca_pa
        }
        pca_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".pca" }}
        pca_plot=dcc.Graph(figure=pca_plot, config=pca_config, style={"width":"100%","overflow-x":"auto"})
        
        iscatter_pca=html.Div( 
        [
            html.Button(id='btn-iscatter_pca', n_clicks=0, children='Scatterplot', 
            style={"margin-top":4, \
                "margin-left":4,\
                "margin-right":4,\
                'background-color': "#5474d8", \
                "color":"white"})
        ])
                
        pca_bol=True
    else:
        pca_bol=False
    

    if lgeneids==0 and (len(selected_sets) > 0 or len(selected_condition)): 
        violin_plot = make_violin_plot(selected_study, selected_genotype, selected_condition, cache)
        violin_config = { 'toImageButtonOptions': { 'filename': download_name+".pseudoage" }, 'displaylogo': False} #'modeBarButtonsToRemove':["toImage"]
        violin_plot = dcc.Graph(figure=violin_plot, config=violin_config,  id="graph")

        violin_age=html.Div( 
        [
            html.Button(id='btn-violin-age', n_clicks=0, children='Violin plot', 
            style={"margin-top":4, \
                "margin-left":4,\
                "margin-right":4,\
                'background-color': "#5474d8", \
                "color":"white"})
        ])
                
        violin_bol=True
    else:
        violin_bol=False
 


    if  (pca_bol) & (gene_expression_bar_bol) :

        minwidth=["Samples", "Expression", "PCA-Clock", "PseudoAge", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)
        bar_plot_=change_fig_minWidth(bar_plot,minwidth)

        out=dcc.Tabs( [ 
                    dcc.Tab([ results_files_, download_samples], 
                            label="Samples", id="tab-samples",
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ pca_plot, iscatter_pca ], 
                            label="PCA-Clock", id="tab-pca", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ violin_plot, violin_age ], 
                            label="PseudoAge", id="tab-age", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ bar_plot_, download_bar], 
                            label="Bar Plot", id="tab-bar", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ gene_expression_, download_geneexp], 
                            label="Expression", id="tab-geneexpression", 
                            style={"margin-top":"0%"}),
                    ],
                    mobile_breakpoint=0,
                    style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif (gene_expression_bol) & (gene_expression_bar_bol) :
        minwidth=["Samples","Expression", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)
        bar_plot_=change_fig_minWidth(bar_plot,minwidth)


        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
             dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif (gene_expression_bol) & pca_bol :

        minwidth=["Samples","Expression", "PCA-Clock"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        pca_plot=change_fig_minWidth(pca_plot,minwidth)

        out=dcc.Tabs( [ 
                    dcc.Tab([ results_files_, download_samples], 
                            label="Samples", id="tab-samples",
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ pca_plot, iscatter_pca ], 
                            label="PCA-Clock", id="tab-pca", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ violin_plot, violin_age ], 
                            label="PseudoAge", id="tab-age", 
                            style={"margin-top":"0%"}),
                    dcc.Tab( [ gene_expression_, download_geneexp], 
                            label="Expression", id="tab-geneexpression", 
                            style={"margin-top":"0%"}),
                    ],  
                    mobile_breakpoint=0,
                    style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
    
    elif gene_expression_bar_bol :

        minwidth=["Samples","Expression", "Bar Plot"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        bar_plot_=change_fig_minWidth(bar_plot,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
             dcc.Tab( [ bar_plot_, download_bar], 
                    label="Bar Plot", id="tab-bar", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    elif gene_expression_bol:

        minwidth=["Samples","Expression"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    else:
        minwidth=["Samples"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        # results_files_=change_table_minWidth(results_files_,minwidth)

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_, 
                        download_samples
                    ], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    #return out
    return out, pca_store


@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Output(component_id='opt-geneids', component_property='options'),
    #Output(component_id='opt-condition', component_property='options'),
    Input('session-id', 'data'),
    #Input('opt-datasets', 'value') 
    )
def update_datasets(session_id):#, datasets):
    #results_files, _ = filter_samples(datasets=datasets, cache=cache)    
    results_files = read_meta_file(cache)    
    datasets=list(set(results_files["study"]))
    datasets=make_options(datasets)

    #results_files = results_files[results_files['study'].isin(datasets)]
    #conditions=list(set(results_files['condition']))
    #conditions=make_options(conditions)

    genes=read_genes(cache)
    geneids=list(set(genes['gene_id']))
    geneids=make_options(geneids)

    return datasets, geneids#, conditions

@dashapp.callback(
    Output(component_id='opt-genotypes', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value') )
def update_groups(session_id, datasets):
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)
    groups_=list(set(selected_results_files["genotype"]))
    groups_=make_options(groups_)
    return groups_

@dashapp.callback(
    Output(component_id='opt-conditions', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value'),
    Input('opt-genotypes', 'value'))
def update_condition(session_id, datasets, genotype):
    selected_results_files, ids2labels = filter_samples(datasets=datasets, genotype=genotype, cache=cache)    
    condition_ = list(set(selected_results_files["condition"]))
    condition_ = make_options(condition_)
    return condition_


@dashapp.callback(
    Output("download-samples", "data"),
    Input("btn-samples", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genotypes", "value"),
    State("opt-conditions", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_samples(n_clicks, datasets, genotype, condition, fileprefix):

    selected_results_files, ids2labels=filter_samples(datasets=datasets,genotype=genotype, condition=condition, cache=cache)    
    results_files=selected_results_files[["study","genotype","condition","time", "PseudoAge"]]
    results_files.columns=["study","genotype","condition","time", "PseudoAge"]
    results_files=results_files.drop_duplicates()
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.samples.xlsx" %fileprefix
    return dcc.send_data_frame(results_files.to_excel, filename, sheet_name="samples", index=False)


@dashapp.callback(
    Output("download-geneexp", "data"),
    Input("btn-geneexp", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genotypes", "value"),
    State("opt-conditions", "value"),
    State("opt-geneids", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_geneexp(n_clicks,datasets, genotype, condition, geneids, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,genotype=genotype, condition=condition, cache=cache)
    gene_expression=filter_gene_expression(ids2labels,geneids,cache)
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.gene_expression.xlsx" %fileprefix
    return dcc.send_data_frame(gene_expression.to_excel, filename, sheet_name="gene exp.", index=False)

@dashapp.callback(
    Output("redirect-pca", 'children'),
    Input("btn-iscatter_pca", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genotypes", "value"),
    State("opt-conditions", "value"),
    State("pca-data-store", "data"),
    prevent_initial_call=True,
)
def pca_to_iscatterplot(n_clicks, datasets, genotype, condition, pca_store):    
    if n_clicks:
        if not pca_store:
            raise PreventUpdate
        
        pca_df = pd.read_json(pca_store["df"])
        pca_pa = pca_store["pa"]

        pca_pa["xcols"]=pca_df.columns.tolist()
        pca_pa["ycols"]=pca_df.columns.tolist()
        # pca_pa["groups"]=["None"]+pca_df.columns.tolist()
        # pca_pa["labels_col"]=["select a column.."]+pca_df.columns.tolist()
        # pca_pa["labels_col_value"]="select a column.."

        session_data={ 
            "APP_VERSION": app.config['APP_VERSION'],
            "PYFLASKI_VERSION": PYFLASKI_VERSION,
            "session_data": 
                {
                    "app": 
                    {
                        "scatterplot": 
                        {
                            "df": pca_df.to_json() ,
                            "filename": "from.datalake.json", 
                            "last_modified": datetime.now().timestamp(), 
                            "pa": pca_pa
                        }
                    }
                }
            }
                        
        session_data=encode_session_app(session_data)
        session["session_data"]=session_data

        sleep(2)

        return dcc.Location(pathname=f"{PAGE_PREFIX}/scatterplot/", id="index")


@dashapp.callback(
    Output("redirect-violin", 'children'),
    Input("btn-violin-age", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genotypes", "value"),
    State("opt-conditions", "value"),
    prevent_initial_call=True,
)
def pseudoage_to_violin(n_clicks, datasets, genotype, condition):
    if not n_clicks:
        raise PreventUpdate

    from datetime import datetime
    from time import sleep

    # Filter data
    selected_results_files, _ = filter_samples(datasets=datasets, genotype=genotype, condition=condition, cache=cache)
    violin_df = selected_results_files[["study", "genotype", "condition", "PseudoAge"]].dropna()

    if violin_df.empty:
        raise PreventUpdate

    # Use default parameters and override values to match the original generated figure
    pa = figure_defaults()
    pa["x_val"] = "condition"
    pa["y_val"] = "PseudoAge"
    # pa["style"] = "Boxplot and Swarmplot"
    pa["style"] = "Boxplot"
    pa["plot_type"] = "box"
    pa["points"] = "false"
    pa["legend_title"] = "Condition"
    pa["ylabel"] = "Biological Age (1.0 = mean life span)"
    pa["title"] = "PseudoAge prediction (Jun2025 ver)"

    # Prepare session data for violinplot app
    session_data = {
        "APP_VERSION": app.config['APP_VERSION'],
        "PYFLASKI_VERSION": PYFLASKI_VERSION,
        "session_data": {
            "app": {
                "violinplot": {
                    "df": violin_df.to_json(),
                    "filename": "from.datalake.prot.json",
                    "last_modified": datetime.now().timestamp(),
                    "pa": pa
                }
            }
        }
    }

    # Encode and store session
    session_data = encode_session_app(session_data)
    session["session_data"] = session_data

    sleep(2)
    return dcc.Location(pathname=f"{PAGE_PREFIX}/violinplot/", id="index")
