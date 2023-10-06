from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from flask_login import current_user
from flask_caching import Cache
import plotly.graph_objects as go
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
# import traceback
import json
import base64
import pandas as pd
# import time
from werkzeug.utils import secure_filename
import humanize
from myapp.models import User
import stat
from datetime import datetime
# import dash_table
import shutil
from time import sleep
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from ._cbioportal import read_results_files, nFormat, plot_gene, filter_data, read_meta_files, read_study_meta, convert_html_links_to_markdown

        
PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("cbioportal",url_base_pathname=f'{PAGE_PREFIX}/cbioportal/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="cBioPortal", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    if "cbioportal" in PRIVATE_ROUTES :
        appdb=PrivateRoutes.query.filter_by(route="cbioportal").first()
        if not appdb:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        allowed_users=appdb.users
        if not allowed_users:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        if current_user.id not in allowed_users :
            allowed_domains=appdb.users_domains
            if current_user.domain not in allowed_domains:
                return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    ## check if user is authorized
    eventlog = UserLogging(email=current_user.email, action="visit cbioportal")
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
            make_navbar_logged("cBioPortal",current_user),
            html.Div(id="app_access"),
            html.Div(id="redirect-lifespan"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),
            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [
                                    html.H5("Filters", style={"margin-top":10}), 
                                    html.Label('Data sets'), make_loading( dcc.Dropdown(id='opt-datasets', multi=True), 1),
                                    dcc.Checklist(options=[{"label":"Significant genes only", "value":'disable'}], value=[], id='sig-only', style={"width":"100%", "margin-top":10}, inputStyle={"margin-right": "10px"}),
                                    html.Label('Gene names',style={"margin-top":10}),  make_loading( dcc.Dropdown( id='opt-genenames', multi=True), 4 ),
                                    html.Label('Lower percentile',style={"margin-top":10}), 
                                    dcc.Input(id='lower_percentile', value="25", type='text',style={"width":"100%", "height":"34px"}),
                                    html.Label('Higher percentile',style={"margin-top":10}), 
                                    dcc.Input(id='higher_percentile', value="75", type='text',style={"width":"100%", "height":"34px"}),
                                    html.Label('Download file prefix',style={"margin-top":10}), 
                                    dcc.Input(id='download_name', value="cbio.portal", type='text',style={"width":"100%", "height":"34px"}),
                                    html.Hr(style={'width' : "100%", "margin-top":"15px", "margin-bottom": "0px"}),
                                    html.Label('Abbreviations:',style={"margin-top":10, "width":"100%"}),
                                    html.Label('N Low -> No. of samples in lower percentile',style={"margin-top":4, "font-size":14}),
                                    html.Label('N High -> No. of samples in upper percentile',style={"margin-top":2, "font-size":14}),
                                    html.Label('LLRT -> Log Likelihood Ratio Test',style={"margin-top":2, "font-size":14}),
                                    html.Label('PHT -> Proportional Hazard Test',style={"margin-top":2, "font-size":14}),
                                    html.Hr(style={'width' : "100%", "margin-top":"15px", "margin-bottom": "0px"}),
                                    dcc.Markdown('''Reference: [cBioPortal](https://www.cbioportal.org/datasets)''', style={"width":"100%", "margin-top":"10px", "margin-bottom": "0px", "height":"20px"})
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
                        sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","height": "100%",'overflow': 'scroll',"margin-bottom":"50px"} 
                    ),               
                    dbc.Col( 
                        dcc.Loading(
                            id="loading-output-2",
                            type="default",
                            children=[ html.Div(id="my-output")],
                            style={"margin-top":"50%","height": "100%"} 
                        ),
                        style={"height": "100%","width": "100%",'overflow': 'scroll',"margin-bottom":"50px"})
                ],
                align="start",
                justify="left",
                className="g-0",
                style={"height":"100%","width":"100%","overflow":"scroll"}
            ),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )

    return protected_content



@dashapp.callback(
    Output('lower_percentile', 'disabled'),
    Output('higher_percentile', 'disabled'),
    Input('session-id', 'data'),
    Input('sig-only','value')
    )
def percentiles_block(session_id, sig_only):

    disabled = 'disable' in sig_only
    #print("dis", disabled)
    return disabled, disabled


@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Input('session-id', 'data')
    )
def update_datasets(session_id):

    meta=read_meta_files(cache)
    meta=meta["short_name"].tolist()
    
    datasets=make_options(meta)

    return datasets


@dashapp.callback(
    Output(component_id='opt-genenames', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value'),
    Input('sig-only', 'value'), )
def update_genes(session_id, datasets, sig_only):
    sub=filter_data(datasets=datasets, cache=cache)
    
    if datasets:
        meta_files=read_meta_files(cache)
        ds_mapping=meta_files[["cancer_study_identifier", "short_name"]]
        datasets=ds_mapping.loc[ ds_mapping["short_name"].isin(datasets), "cancer_study_identifier"].tolist()
   
        sub=filter_data(datasets=datasets, cache=cache)

    if len(sig_only) > 0 and sig_only[0] == 'disable':
        sub=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05)]
    
    genes_=list(set( sub["Hugo Symbol"].tolist() ))
    genes=make_options(genes_)
    return genes


################################################################################

## all callback elements with `State` will be updated only once submit is pressed
## all callback elements wiht `Input` will be updated everytime the value gets changed 
@dashapp.callback(
    Output('my-output','children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-datasets", "value"),
    State("opt-genenames", "value"),
    State("lower_percentile", "value"),
    State("higher_percentile", "value"),
    State('sig-only', 'value'),
    State('download_name','value'),
)
def update_output(session_id, n_clicks, datasets, genenames, lower_pc, higher_pc, sig_only, download_name): #, geneids:
    
    meta_files_or=read_meta_files(cache=cache)
    meta_files=meta_files_or[["type_of_cancer", "cancer_study_identifier", "name", "citation" ]]
    meta_files_=make_table(meta_files, "meta_files")
    download_meta=html.Div( 
        [
            html.Button(id='btn-meta', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-meta")
        ]
    )

    if datasets:
        ds_mapping=meta_files_or[["cancer_study_identifier", "short_name"]]
        datasets=ds_mapping.loc[ ds_mapping["short_name"].isin(datasets), "cancer_study_identifier"].tolist()
    
    selected_results_files=filter_data(datasets=datasets, cache=cache)
    results_files=selected_results_files

    results_files_=make_table(results_files,"results_files")
    download_samples=html.Div( 
        [
            html.Button(id='btn-samples', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-samples")
        ]
    )

    # print(len(sig_only))
    # print(sig_only)
    
    #if len(sig_only) > 0 and sig_only[0] == True:
    if len(sig_only) > 0 and sig_only[0] == 'disable':
        results_files_sig=results_files.loc[ (results_files["P.adj(LLRT)"].astype(float) < 0.05) & (results_files["P.Value(PHT)"].astype(float) >= 0.05)]
        results_files_sig_=make_table(results_files_sig, "results_sig")
        sig_bol=True
    else:
        sig_bol=False

    #if datasets and (len(sig_only) > 0 and sig_only[0]) == True:
    if datasets and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[results_files["Dataset"].isin(datasets)]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]
        result_files_ds_sig_genes=make_table(sub_, "results_ds_sig")
        ds_sig_bol=True
    else:
        ds_sig_bol=False

    if datasets and genenames and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[(results_files["Dataset"].isin(datasets)) & (results_files["Hugo Symbol"].isin(genenames))]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]
        result_files_ds_genes_sig_genes=make_table(sub_, "results_ds_gene_sig")
        ds_gene_sig_bol=True
    else:
        ds_gene_sig_bol=False

    if genenames and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[results_files["Hugo Symbol"].isin(genenames)]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]
        result_files_genes_sig_genes=make_table(sub_, "results_ds_sig")
        genes_sig_bol=True
    else:
        genes_sig_bol=False


    if datasets:
        results_files_ds=results_files.loc[results_files["Dataset"].isin(datasets)]
        results_files_ds_=make_table(results_files_ds, "results_ds_files")
        ds_bol=True
    else:
        ds_bol=False


    if genenames:
        results_files_gene=results_files.loc[results_files["Hugo Symbol"].isin(genenames)]
        # print(results_files_gene)
        results_files_gene_=make_table(results_files_gene, "results_gene_files")

        gene_bol=True
    else:
        gene_bol=False

    
    if datasets and genenames:
        results_files_ds_gene=results_files[ results_files['Dataset'].isin( datasets ) & (results_files['Hugo Symbol'].isin( genenames )) ]
        results_files_ds_gene_=make_table(results_files_ds_gene, "results_ds_files")
        dg_bol=True
    else:
        dg_bol=False


    if (datasets and len(datasets) == 1) and (genenames and len(genenames) == 1):
        ds=datasets[0]
        #print(ds)

        df, fig, cph_coeff, cph_stats,args, input_df=plot_gene(genenames, ds, lp=lower_pc, hp=higher_pc) #results_files

        tmp=cph_coeff[[s for s in cph_coeff.columns.tolist() if "cmp" not in s]].T
        tmp=tmp.reset_index(drop=False)
        tmp.columns=["Statistic","Value"]
        cph_stats_=cph_stats.loc[cph_stats["Statistic"].isin([s for s in cph_stats["Statistic"].tolist() if "log rank" not in s])]
        test=pd.concat([cph_stats_,tmp])
        test["Value"]=test["Value"].apply(lambda x : nFormat(x) if isinstance(x, (float, int)) else x)
        
        readme_cols='''
        **baseline estimation**

        Method used to estimate baseline hazard 

        **partial log-likelihood**

        Represents how well the model fits the observed survival data given the model's parameter estimates. 
        A higher log partial likelihood value indicates a better fit to the data compared to a lower value.

        **Concordance**

        Concordance or the C-Index quantifies the ability of the model to correctly rank the survival times of pairs of subjects. 
        It is a measure of the model's ability to stratify subjects into groups based on their risk.
        
        The C-Index ranges from 0.5 to 1.0

        - 0.5 is the expected result from random predictions
        - 1.0 is perfect concordance

        **Partial AIC**

        Represents the trade-off between model fit and model complexity. It quantifies how much better the model fits the data compared to its complexity.
        A Lower Partial AIC indicates that a model strikes a good balance (compared to a higer value) between explaining the data and avoiding unnecessary complexity.

        **log-likelihood ratio test**

        Tests the goodness of fit of a model. Compares the existing model (with all covariates) to the trivial model of no covariates.

        If the P.value < 0.05, the null hypothesis (complex model is not better than the trivial model) is rejected in favor of the 
        alternative hypothesis (complex model is significantly better). 
        This indicates that the additional covariates or constraints in the alternative model significantly improve the model fit.

        **proportional-hazard-test**

        Tests whether the assumption of constant hazard ratios over time from the Cox's proportional hazard model is met.
        P.Value >= 0.05 suggests that the assumption is met.


        **covariate**

        Indicates the variables that were used as covariates in the Cox regression model.

        **coef**

        Represents the estimated coefficients (log hazard ratios) associated with each covariate. 
        These coefficients quantify the change in the log hazard for a one-unit change in the corresponding covariate while holding other covariates constant.

        **exp(coef)**

        Exponentiated coefficients which correspond to the hazard ratios (HRs). 
        The hazard ratio represents the ratio of the hazard rate for one group or level of a covariate to another group or level. 
        It quantifies the relative change in hazard associated with a one-unit change in the covariate.

        **se(coef)**

        Standard error of the coefficient estimates. It measures the uncertainty or variability in the coefficient estimates.

        **coef lower 95%**

        Lower bound of the 95% confidence interval for the coefficient estimate. 
        It indicates the range within which the true coefficient value is likely to fall with 95% confidence.

        **coef upper 95%**

        Upper bound of the 95% confidence interval for the coefficient estimate. 
        Also indicates the range within which the true coefficient value is likely to fall with 95% confidence.


        **exp(coef) lower 95%**

        Lower bound of the 95% confidence interval for the hazard ratio (exp(coef)).

        **exp(coef) upper 95%**

        Upper bound of the 95% confidence interval for the hazard ratio (exp(coef)).

        **z**

        The z-statistic is a measure of how many standard errors the coefficient estimate is away from zero. 
        It is calculated as the coefficient estimate divided by its standard error.

        **p**

        The P.value associated with the z-statistic. It tests the null hypothesis that the coefficient (or hazard ratio) is equal to zero (i.e., no effect). 
        P.Value < 0.05 suggests that the covariate has a significant effect on survival.

        **-log2(p)**

        This is a transformation of the P.value. Taking the negative base-2 logarithm (-log2) helps emphasize the significance of small p-values. 
        Larger values indicate stronger evidence against the null hypothesis.

        **Study Metadata**

        '''

        meta_list=read_study_meta(dataset=ds)
        meta_list_formatted=[convert_html_links_to_markdown(s) for s in meta_list]
        meta_mds=[dcc.Markdown(text, style={"width":"90%", "margin":"10px"}) for text in meta_list_formatted]
        
        readme=dcc.Markdown(readme_cols, style={"width":"90%", "margin":"10px"} )
        output_df=make_table(test, "gene_ds_specific_table")
        surv_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".km" }}
        fig_plot=dcc.Graph(figure=fig, config=surv_config, style={"width":"100%","overflow-x":"auto"})
        
        lifespan_app_tab2=html.Div( 
        [         
            html.Button(id='btn-lifespan-app', n_clicks=0, children='Lifespan', 
            style={"margin-top":4, \
                "margin-left":4,\
                "margin-right":4,\
                'background-color': "#5474d8", \
                "color":"white"
                })
        ]) 
        
        surv_fig_bol = True
    else:
        surv_fig_bol = False

    ######################################################################################################################

    if (ds_bol) & (gene_bol) & surv_fig_bol:
        minwidth=["Lifespan curve","Survival Analysis","Readme", "Studies"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        #results_files_=change_table_minWidth(results_files_,minwidth)
        results_files_=change_table_minWidth(output_df, minwidth)
        fig_plot_=change_fig_minWidth(fig_plot,minwidth)

        out=dcc.Tabs(
            [ 
                dcc.Tab( [ fig_plot_, lifespan_app_tab2],
                        label="Lifespan curve", id="tab-survPLOT", 
                        style={"margin-top":"0%"}),
                dcc.Tab([ results_files_, download_samples], 
                        label="Survival Analysis", id="tab-samples",
                        style={"margin-top":"0%"}),
                dcc.Tab( [readme]+meta_mds, label="Readme", id="tab-readme") ,
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat") ,

            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
        

    ####################################################################

    elif ds_gene_sig_bol:
        # print(ds_gene_sig_bol)
        minwidth=["Significant genes in the selected genes and datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [
                        result_files_ds_genes_sig_genes, 
                        download_samples
                    ], 
                    label="Significant genes in the selected genes and datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )


    ####################################################################
        
    elif dg_bol:
        # print(dg_bol)
        minwidth=["Selected genes and datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_ds_gene_, 
                        download_samples
                    ], 
                    label="Selected Genes and Datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
        
    ####################################################################

    elif genes_sig_bol:
        # print(genes_sig_bol)
        minwidth=["Significant genes from the selected genes"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        result_files_genes_sig_genes, 
                        download_samples
                    ], 
                    label="Significant genes from the selected genes", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_ , download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )



    ####################################################################
        
    elif ds_sig_bol:
        # print(ds_sig_bol)
        minwidth=["Significant genes in selected datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        result_files_ds_sig_genes, 
                        download_samples
                    ], 
                    label="Significant genes in selected datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    ####################################################################  

    elif sig_bol:
        # print(sig_bol)
        minwidth=["Significant genes in all datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_sig_, 
                        download_samples
                    ], 
                    label="Significant genes in all datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
        
    ####################################################################

    elif ds_bol :
        # print(ds_bol)
        minwidth=["Selected datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_ds_, 
                        download_samples
                    ], 
                    label="Selected datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_,download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
        
    ####################################################################
    
    elif gene_bol:
        # print(gene_bol)
        minwidth=["Selected genes"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_gene_, 
                        download_samples
                    ], 
                    label="Selected genes", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat") ,
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    ###################################################################

    else:
        minwidth=["Genes and Datasets"]
        # minwidth=len(minwidth) * 150
        # minwidth = str(minwidth) + "px"

        out=dcc.Tabs( 
            [ 
                dcc.Tab(
                    [ 
                        results_files_, 
                        download_samples
                    ], 
                    label="Genes and Datasets", id="tab-samples",
                    style={"margin-top":"0%"}
                ),
                dcc.Tab( [meta_files_, download_meta], label="Studies", id="tab-metadat")
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
        
    return out


@dashapp.callback(
    Output("redirect-lifespan", 'children'),
    Input("btn-lifespan-app", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genenames", "value"),
    State("lower_percentile", "value"),
    State("higher_percentile", "value"),
    prevent_initial_call=True,
)
def cbioportal_to_lifespan(n_clicks,datasets, genenames, lp,hp ):
    if n_clicks:
        if datasets:
            meta_files_or=read_meta_files(cache=cache)
            ds_mapping=meta_files_or[["cancer_study_identifier", "short_name"]]
            datasets=ds_mapping.loc[ ds_mapping["short_name"].isin(datasets), "cancer_study_identifier"].tolist()

        df, fig, cph_coeff, cph_stats,args, df_input=plot_gene(gene_list=genenames, dataset=datasets[0], lp=lp, hp=hp)

        args['xvals'] =  "day"
        args['yvals'] = "status"

        session_data={ 
            "APP_VERSION": app.config['APP_VERSION'],
            "session_data": 
                {
                    "app": 
                    {
                        "lifespan": 
                        {
                            "df": df_input.to_json() ,
                            "filename": "from.cbioportal.json", 
                            "last_modified": datetime.now().timestamp(), 
                            "pa": args
                        }
                    }
                }
            }
                        
        session_data=encode_session_app(session_data)
        session["session_data"]=session_data
        from time import sleep
        sleep(2)

        return dcc.Location(pathname=f"{PAGE_PREFIX}/lifespan/", id="index")
    

@dashapp.callback(
    Output("download-meta", "data"),
    Input("btn-meta", "n_clicks"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_meta(n_clicks,fileprefix):
    
    meta_files_or=read_meta_files(cache=cache)
    meta_files=meta_files_or[["type_of_cancer", "cancer_study_identifier", "name", "citation" ]]
    
    results_files_to_save=meta_files
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.studies.meta.data.xlsx" %fileprefix

    return dcc.send_data_frame(results_files_to_save.to_excel, filename, sheet_name="cbioportal.studies", index=False)

@dashapp.callback(
    Output("download-samples", "data"),
    Input("btn-samples", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-genenames", "value"),
    State("lower_percentile", "value"),
    State("higher_percentile", "value"),
    State('sig-only', 'value'),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_samples(n_clicks,datasets,genenames, low_perc, high_perc, sig_only, fileprefix):

    meta_files_or=read_meta_files(cache=cache)
    if datasets:
        ds_mapping=meta_files_or[["cancer_study_identifier", "short_name"]]
        datasets=ds_mapping.loc[ ds_mapping["short_name"].isin(datasets), "cancer_study_identifier"].tolist()
    
    selected_results_files=filter_data(datasets=datasets, genes=genenames, cache=cache)
    
    results_files=selected_results_files

    results_files_to_save=results_files
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.datasets.genes.xlsx" %fileprefix


    if (datasets and len(datasets) == 1) and (genenames and len(genenames) == 1):
        df, fig, cph_coeff, cph_stats,args, input_df=plot_gene(genenames, datasets[0], lp=low_perc, hp=high_perc)

        tmp=cph_coeff.T
        tmp=tmp.reset_index(drop=False)
        tmp.columns=["Statistic","Value"]
        test=pd.concat([cph_stats,tmp])
        # print(test)

        ds=datasets[0]
        g=genenames[0]

        results_files_to_save=test
        fileprefix=secure_filename(str(fileprefix))
        filename="%s.%s.%s.xlsx" % (fileprefix , ds , g)

    if len(sig_only) > 0 and sig_only[0] == 'disable':
        results_files_sig=results_files.loc[ (results_files["P.adj(LLRT)"].astype(float) < 0.05) & (results_files["P.Value(PHT)"].astype(float) >= 0.05)]
        
        results_files_to_save=results_files_sig
        fileprefix=secure_filename(str(fileprefix))
        filename="%s.sig.genes.xlsx" %fileprefix


    if datasets and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[results_files["Dataset"].isin(datasets)]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]
        
        results_files_to_save=sub_
        fileprefix=secure_filename(str(fileprefix))
        filename="%s.sub.datasets.sig.genes.xlsx" %fileprefix

    if datasets and genenames and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[(results_files["Dataset"].isin(datasets)) & (results_files["Hugo Symbol"].isin(genenames))]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]
        
        results_files_to_save=sub_
        fileprefix=secure_filename(str(fileprefix))
        filename="%s.sub.datasets.genes.sig.xlsx" %fileprefix

    if genenames and (len(sig_only) > 0 and sig_only[0]) == 'disable':
        sub=results_files.loc[results_files["Hugo Symbol"].isin(genenames)]
        sub_=sub.loc[ (sub["P.adj(LLRT)"].astype(float) < 0.05) & (sub["P.Value(PHT)"].astype(float) >= 0.05) ]

        results_files_to_save=sub_
        fileprefix=secure_filename(str(fileprefix))
        filename="%s.sub.genes.sig.xlsx" %fileprefix

    return dcc.send_data_frame(results_files_to_save.to_excel, filename, sheet_name="cbioportal", index=False)



@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

