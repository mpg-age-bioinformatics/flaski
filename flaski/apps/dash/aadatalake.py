from flaski import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, parse_table, protect_dashviews, validate_user_access, \
    make_navbar, make_footer, make_options, make_table, META_TAGS, make_min_width, \
    change_table_minWidth, change_fig_minWidth
from ._aadatalake import read_results_files, read_gene_expression, read_genes, read_significant_genes, \
    filter_samples, filter_genes, filter_gene_expression, nFormat, read_dge, make_volcano_plot, make_ma_plot
import uuid
from werkzeug.utils import secure_filename

# import pandas as pd
import os

CURRENTAPP="aadatalake"
navbar_title="RNAseq data lake"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})

controls = [ 
    html.H5("Filters", style={"margin-top":10}), 
    html.Label('Data sets'), dcc.Dropdown( id='opt-datasets', multi=True),
    html.Label('Groups',style={"margin-top":10}), dcc.Dropdown( id='opt-groups', multi=True),
    html.Label('Samples',style={"margin-top":10}), dcc.Dropdown( id='opt-samples', multi=True),
    html.Label('Gene names',style={"margin-top":10}), dcc.Dropdown( id='opt-genenames', multi=True),
    html.Label('Gene IDs',style={"margin-top":10}), dcc.Dropdown( id='opt-geneids', multi=True),
    html.Label('Download file prefix',style={"margin-top":10}), dcc.Input(id='download_name', value="data.lake", type='text') ]

side_bar=[ dbc.Card(controls, body=True),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%","margin-top":4, "margin-bottom":4} )
         ]

# Define Layout
dashapp.layout = html.Div( [ html.Div(id="navbar"), dbc.Container(
    fluid=True,
    children=[
        html.Div(id="app_access"),
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dbc.Row(
            [
                dbc.Col( dcc.Loading( 
                        id="loading-output-1",
                        type="default",
                        children=html.Div(id="side_bar"),
                        style={"margin-top":"0%"}
                    ),                    
                    md=3, style={"height": "100%",'overflow': 'scroll'} ),               
                dbc.Col( dcc.Loading(
                        id="loading-output-2",
                        type="default",
                        children=html.Div(id="my-output"),
                        style={"margin-top":"50%","height": "100%"}
                    ),                    
                    md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"min-height": "87vh"}), # "height":"87vh"
    ] ) 
    ] + make_footer()
)

## all callback elements with `State` will be updated only once submit is pressed
## all callback elements wiht `Input` will be updated everytime the value gets changed 
@dashapp.callback(
    Output(component_id='my-output', component_property='children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State(component_id='download_name', component_property='value'),
)
def update_output(session_id, n_clicks, datasets, groups, samples, genenames, geneids, download_name):
    if not validate_user_access(current_user,CURRENTAPP):
        return None

    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    
    ## samples
    results_files=selected_results_files[["Set","Group","Reps"]]
    results_files.columns=["Set","Group","Sample"]
    results_files=results_files.drop_duplicates()      
    results_files_=make_table(results_files,"results_files")
    # results_files_ = dbc.Table.from_dataframe(results_files, striped=True, bordered=True, hover=True)
    download_samples=html.Div( 
        [
            html.Button(id='btn-samples', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
            dcc.Download(id="download-samples")
        ]
    )

    ## gene expression
    if datasets or groups or samples or  genenames or  geneids :
        gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)
        gene_expression_=make_table(gene_expression,"gene_expression")#,fixed_columns={'headers': True, 'data': 2} )
        # gene_expression_ = dbc.Table.from_dataframe(gene_expression, striped=True, bordered=True, hover=True)
        download_geneexp=html.Div( 
            [
                html.Button(id='btn-geneexp', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                dcc.Download(id="download-geneexp")
            ]
        )
        gene_expression_bol=True
    else:
        gene_expression_bol=False

    
    ## differential gene expression
    dge_bol=False
    volcano_plot=None
    if not samples:
        dge_datasets=list(set(selected_results_files["Set"]))
        if len(dge_datasets) == 1 :
            dge_groups=list(set(selected_results_files["Group"]))
            if len(dge_groups) == 2:
                dge=read_dge(dge_datasets[0], dge_groups, cache)
                dge_plots=dge.copy()
                if genenames:
                    dge=dge[dge["gene name"].isin(genenames)]                    
                if geneids:
                    dge=dge[dge["gene id"].isin(geneids)]

                dge_=make_table(dge,"dge")
                download_dge=html.Div( 
                                [
                                    html.Button(id='btn-dge', n_clicks=0, children='Download', style={"margin-top":4, 'background-color': "#5474d8", "color":"white"}),
                                    dcc.Download(id="download-dge")
                                ]
                            )

                annotate_genes=[]
                if genenames:
                    genenames_=dge[dge["gene name"].isin(genenames)]["gene name"].tolist()
                    annotate_genes=annotate_genes+genenames_
                if geneids:
                    genenames_=dge[dge["gene id"].isin(geneids)]["gene name"].tolist()
                    annotate_genes=annotate_genes+genenames_                

                volcano_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".volcano" }}
                volcano_plot, volcano_pa=make_volcano_plot(dge_plots, dge_datasets[0], annotate_genes)
                volcano_plot=dcc.Graph(figure=volcano_plot, config=volcano_config, style={"width":"100%","overflow-x":"auto"})

                ma_config={ 'toImageButtonOptions': { 'format': 'svg', 'filename': download_name+".ma" }}
                ma_plot, ma_pa=make_ma_plot(dge_plots, dge_datasets[0],annotate_genes )
                ma_plot=dcc.Graph(figure=ma_plot, config=ma_config, style={"width":"100%","overflow-x":"auto"})

                dge_bol=True

    if dge_bol:

        minwidth=["Samples","Expression","DGE","Volcano","MA"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        results_files_=change_table_minWidth(results_files_,minwidth)
        gene_expression_=change_table_minWidth(gene_expression_,minwidth)
        dge_=change_table_minWidth(dge_,minwidth)

        volcano_plot=change_fig_minWidth(volcano_plot,minwidth)
        ma_plot=change_fig_minWidth(ma_plot,minwidth)

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples], 
                    label="Samples", id="tab-samples",
                    style={"margin-top":"0%"}),
            dcc.Tab( [ gene_expression_, download_geneexp], 
                    label="Expression", id="tab-geneexpression", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ dge_, download_dge], 
                    label="DGE", id="tab-dge", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ volcano_plot ], 
                    label="Volcano", id="tab-volcano", 
                    style={"margin-top":"0%"}),
            dcc.Tab( [ ma_plot ], 
                    label="MA", id="tab-ma", 
                    style={"margin-top":"0%"})
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
            
    elif gene_expression_bol:

        minwidth=["Samples","Expression"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"

        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples
            ], label="Samples", id="tab-samples",style={"margin-top":"0%"}), 
            dcc.Tab( [ gene_expression_, download_geneexp], label="Expression", id="tab-geneexpression", style={"margin-top":"0%"})
            ],  
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )

    else:
        minwidth=["Samples"]
        minwidth=len(minwidth) * 150
        minwidth = str(minwidth) + "px"
        out=dcc.Tabs( [ 
            dcc.Tab([ results_files_, download_samples ], 
            label="Samples", id="tab-samples",style={"margin-top":"0%"}), 
            ],
            mobile_breakpoint=0,
            style={"height":"50px","margin-top":"0px","margin-botom":"0px", "width":"100%","overflow-x":"auto", "minWidth":minwidth} )
    
    return out

@dashapp.callback(
    Output("download-samples", "data"),
    Input("btn-samples", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_samples(n_clicks,datasets, groups, samples, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    results_files=selected_results_files[["Set","Group","Reps"]]
    results_files.columns=["Set","Group","Sample"]
    results_files=results_files.drop_duplicates()
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.samples.xlsx" %fileprefix
    return dcc.send_data_frame(results_files.to_excel, filename, sheet_name="samples", index=False)

@dashapp.callback(
    Output("download-geneexp", "data"),
    Input("btn-geneexp", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_geneexp(n_clicks,datasets, groups, samples, genenames, geneids, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.gene_expression.xlsx" %fileprefix
    return dcc.send_data_frame(gene_expression.to_excel, filename, sheet_name="gene exp.", index=False)

@dashapp.callback(
    Output("download-dge", "data"),
    Input("btn-dge", "n_clicks"),
    State("opt-datasets", "value"),
    State("opt-groups", "value"),
    State("opt-samples", "value"),
    State("opt-genenames", "value"),
    State("opt-geneids", "value"),
    State('download_name', 'value'),
    prevent_initial_call=True,
)
def download_dge(n_clicks,datasets, groups, samples, genenames, geneids, fileprefix):
    selected_results_files, ids2labels=filter_samples(datasets=datasets,groups=groups, reps=samples, cache=cache)    
    gene_expression=filter_gene_expression(ids2labels,genenames,geneids,cache)

    if not samples:
        dge_datasets=list(set(selected_results_files["Set"]))
        if len(dge_datasets) == 1 :
            dge_groups=list(set(selected_results_files["Group"]))
            if len(dge_groups) == 2:
                dge=read_dge(dge_datasets[0], dge_groups, cache, html=False)
                if genenames:
                    dge=dge[dge["gene name"].isin(genenames)]                    
                if geneids:
                    dge=dge[dge["gene id"].isin(geneids)]
    fileprefix=secure_filename(str(fileprefix))
    filename="%s.dge.xlsx" %fileprefix
    return dcc.send_data_frame(dge.to_excel, filename, sheet_name="dge", index=False)

@dashapp.callback(
    Output(component_id='opt-datasets', component_property='options'),
    Output(component_id='opt-genenames', component_property='options'),
    Output(component_id='opt-geneids', component_property='options'),
    Input('session-id', 'data')
    )
def update_datasets(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    results_files=read_results_files(cache)
    datasets=list(set(results_files["Set"]))
    datasets=make_options(datasets)

    genes=read_genes(cache)

    genenames=list(set(genes["gene_name"]))
    genenames=make_options(genenames)

    geneids=list(set(genes["gene_id"]))
    geneids=make_options(geneids)

    return datasets, genenames, geneids

@dashapp.callback(
    Output(component_id='opt-groups', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value') )
def update_groups(session_id, datasets):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)    
    groups_=list(set(selected_results_files["Group"]))
    groups_=make_options(groups_)
    return groups_

@dashapp.callback(
    Output(component_id='opt-samples', component_property='options'),
    Input('session-id', 'data'),
    Input('opt-datasets', 'value'),
    Input('opt-groups', 'value') )
def update_reps(session_id, datasets, groups):
    if not validate_user_access(current_user,CURRENTAPP):
        return None
    selected_results_files, ids2labels=filter_samples(datasets=datasets, cache=cache)    
    groups_=list(set(selected_results_files["Group"]))
    groups_=make_options(groups_)

    selected_results_files, ids2labels=filter_samples(datasets=datasets, groups=groups,cache=cache)    
    reps_=list(set(selected_results_files["Reps"]))
    reps_=make_options(reps_)

    return reps_

# this call back prevents the side bar from being shortly 
# show / exposed to users without access to this App
@dashapp.callback( Output('app_access', 'children'),
                   Output('side_bar', 'children'),
                   Output('navbar','children'),
                   Input('session-id', 'data') )
def get_side_bar(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return dcc.Location(pathname="/index", id="index"), None, None
    else:
        navbar=make_navbar(navbar_title, current_user, cache)
        return None, side_bar, navbar

@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

# if __name__ == '__main__':
#     app.run_server(host='0.0.0.0', debug=True, port=8050)

# #### HANDLING LARGE AMOUNT OF ARGUMENTS ####
# #### this will work for inputs with only one present in the list of Inputs+States
# ## all callback elements with `State` will be updated only once submit is pressed
# ## all callback elements wiht `Input` will be updated everytime the value gets changed 
# inputs=[Input('submit-button-state', 'n_clicks')]
# states=[State('upload-data', 'contents'),
#     State("opt-xcol", "search_value"),
#     State(component_id='multiplier', component_property='value'),
#     State('upload-data', 'filename'),
#     State('upload-data', 'last_modified') ]
# @app.callback(
#     Output(component_id='my-output', component_property='children'),
#     inputs,
#     states
#     )      
# def update_output(*args):
#     input_names = [item.component_id for item in inputs + states]
#     kwargs_dict = dict(zip(input_names, args))
#     print(kwargs_dict)
#     multiplier=kwargs_dict["multiplier"]