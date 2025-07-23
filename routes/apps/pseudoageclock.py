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
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, encode_session_app
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
from myapp.models import UserLogging, PrivateRoutes
from time import sleep
from ._pseudoageclock import inference as pseudoage_inference


PYFLASKI_VERSION=1#os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("protclock",url_base_pathname=f'{PAGE_PREFIX}/protclock/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="PseudoAge Clock", assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
        dcc.Location( id='url', refresh=True ),
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
    # Check if user is authorized
    if "protclock" in PRIVATE_ROUTES :
        appdb=PrivateRoutes.query.filter_by(route="protclock").first()
        if not appdb:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        allowed_users=appdb.users
        if not allowed_users:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        if current_user.id not in allowed_users :
            allowed_domains=appdb.users_domains
            if current_user.domain not in allowed_domains:
                return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    eventlog = UserLogging(email=current_user.email, action="visit protclock")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("PseudoAge: Biological age prediction with single-worm proteomics",current_user),
            html.Div(id="app-content"),
            navbar_A,
            html.Div(id="redirect-violin"),
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
                dbc.Row([
                    dbc.Col([
                        html.Div(
                            dbc.Label("Input file"),
                        ),
                    ]),
                    dbc.Col([
                            dbc.Button(
                                html.Span(
                                    [ 
                                        html.I(className="  fas fa-file-excel"), #, style={"size":"12px"}
                                        " Example" 
                                    ]
                                ),
                                n_clicks=0,
                                id='example-session-btn', 
                                color="primary",
                                style={"width":"100%"}
                            ),
                            dcc.Download(id="example-session")
                        ],
                        id="example-session-div",
                        width=3,
                    ),
                ]),
#
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
                                    dbc.Label("WormbaseID column"),
                                    dcc.Dropdown( placeholder="WormbaseID", id='x_val', multi=False)
                                ],
                            # ),
                            width=12,
                            style={"padding-right":"4px"}
                        ),
                    ],
                    align="start",
                    justify="betweem",
                    className="g-0",
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
                ),
    ]

    output_bar = [
        dcc.Loading(
            id="loading-fig-output",
            type="default",
            children=[
                html.Div(id="fig-output"),
                dcc.Store(id='outdf_'),

                html.Div(
                    [
                        dbc.Button(
                            html.Span(["To violin plot"]),
                            id='btn-violin-age',
                            style={"max-width":"150px","width":"100%"},
                            color="secondary"
                        ),
                    ],
                    id="to-violin-div",
                    style={"max-width":"150px","width":"100%","margin":"4px", 'display': 'none'} # 'none' / 'inline-block'
                ),
                html.Div( 
                    [
                        dbc.Button(
                            html.Span(
                                [ 
                                    "Results Download" 
                                ]
                            ),
                            id='download-result-btn',
                            style={"max-width":"450px","width":"200%"},
                            color="secondary"
                        ),
                        dcc.Download(id="download-result")
                    ],
                    id="download-result-div",
                    style={"max-width":"450px","width":"200%","margin":"4px", 'display': 'none'} # 'none' / 'inline-block'
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
    ]

   

    app_content=html.Div([
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
                    output_bar,
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
                                dcc.Input(id='pdf-filename', value="pseudoage.pdf", type='text', style={"width":"100%"})
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
                                dcc.Input(id='export-filename', value="psueoage.json", type='text', style={"width":"100%"})
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
                ),

                dbc.Modal(
                    [
                        dbc.ModalHeader("File name"), # dbc.ModalTitle(
                        dbc.ModalBody(
                            [
                                dcc.Input(id='result-filename', value="pseudoage.xlsx", type='text', style={"width":"100%"})
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Download", id="result-filename-download", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="result-filename-modal",
                    is_open=False,
                ),
            ],
        align="start",
        justify="left",
        className="g-0",
        style={"height":"86vh","width":"100%","overflow":"scroll"}
        ),
    ])
    return app_content


#example reading session from server storage
@dashapp.callback( 
    Output('upload-data', 'contents'),
    Output('upload-data', 'filename'),
    Output('upload-data', 'last_modified'),
    Input('session-id', 'data'))
def read_session_redis(session_id):
    if "session_data" in list( session.keys() )  :
        imp=session["session_data"]
        del(session["session_data"])
        sleep(2)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update


@dashapp.callback( 
    [Output('x_val', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    Output('x_val', 'value')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    #prevent_initial_call=True
    )
def read_input_file(contents,filename,last_modified,session_id):
    if not filename :
        raise dash.exceptions.PreventUpdate

    try:
        if filename.split(".")[-1] == "json":
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "protclock")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            try:
                x_val = app_data["pa"]["x_val"]
                if x_val not in cols:
                    x_val = cols[0]  # fallback to first column
            except Exception:
                x_val = cols[0]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"protclock")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            x_val=cols[0]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [ cols_, upload_text, None, None,  x_val]

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"protclock")
        return [ dash.no_update, dash.no_update, toast, tb_str, dash.no_update ]





@dashapp.callback( 
    Output('fig-output', 'children'),
    Output('outdf_', 'data'),
    Output('toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    Output('to-violin-div', 'style'),
    Output('download-result-div', 'style'),
    Output('export-session','data'),
    Input("submit-button-state", "n_clicks"),
    Input("export-filename-download","n_clicks"),
    Input("save-session-btn","n_clicks"),
    Input("saveas-session-btn","n_clicks"),
    State('x_val', 'value'),
    [State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('export-filename','value'),
    State('upload-data-text', 'children')],
    prevent_initial_call=True
    )
def make_fig_output(
        n_clicks,
        export_click,
        save_session_btn,
        saveas_session_btn,
        gene_id_column,
        session_id,
        contents,
        filename,
        last_modified,
        export_filename,
        upload_data_text
    ):
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
        df=parse_table(contents,filename,last_modified,current_user.id,cache,"protclock")

        out_df = pseudoage_inference(df, gene_id_column, cache)

        session_data={ "session_data": {"app": { "protclock": {"filename":upload_data_text ,'last_modified':last_modified,"df":df.reset_index().to_json(), "pa": { "x_val": gene_id_column }} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data["PYFLASKI_VERSION"]=PYFLASKI_VERSION
            
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"protclock")
        return dash.no_update, dash.no_update,toast, None, tb_str, download_buttons_style_hide, download_buttons_style_hide, None 
    
    if button_id == "export-filename-download" :
            if not export_filename:
                export_filename="psueoageck.json"
            export_filename=secure_filename(export_filename)
            if export_filename.split(".")[-1] != "json":
                export_filename=f'{export_filename}.json'  

            def write_json(export_filename,session_data=session_data):
                export_filename.write(json.dumps(session_data).encode())
            
            return dash.no_update, dash.no_update, None, None, None, dash.no_update, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    if button_id == "save-session-btn" :
        try:
            if filename and filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, dash.no_update, toast, None, None, dash.no_update, dash.no_update, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, None, dash.no_update, dash.no_update, None
            
        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"protclock")
            return dash.no_update, dash.no_update, toast, None, tb_str, dash.no_update, dash.no_update, None
        
    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update, None, dash.no_update, dash.no_update, None

    if n_clicks > 0:
        try:
            fig = go.Figure( )
            fig = px.box(out_df, x='condition', y='PseudoAge', color='condition', points='all')
            fig.update_layout(
                    title={
                        'text': "PseudoAge inference",
                        'xanchor': 'left',
                        'yanchor': 'top' ,
                        "font": {"size": 25, "color":"black"  } } )
            fig_config={ 'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}
            fig=dcc.Graph(figure=fig,config=fig_config,  id="graph")

            # changed
            # return fig, None, session_data, None, download_buttons_style_show
            # as session data is no longer required for downloading the figure

            eventlog = UserLogging(email=current_user.email,action="display figure protclock")
            db.session.add(eventlog)
            db.session.commit()

            return fig, out_df.to_json(date_format='iso', orient='split'), None, None, None, download_buttons_style_show, download_buttons_style_show,  None

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"protclock")
            return dash.no_update, dash.no_update,toast, session_data, tb_str, download_buttons_style_hide, download_buttons_style_hide, None

    return dash.no_update, dash.no_update, None, None, None, download_buttons_style_hide, download_buttons_style_hide, None


@dashapp.callback(
    Output('example-session', 'data'),
    Input('example-session-btn',"n_clicks"),
    prevent_initial_call=True,
)
def download_example(n_clicks):
    if n_clicks is None or n_clicks == 0:
        return
    example_filename="example_for_pseudoage.xlsx"

    eventlog = UserLogging(email=current_user.email,action="download example input for pseudoage")
    db.session.add(eventlog)
    db.session.commit()

    for_outdf = []
    for i in range(10):
        for_outdf.append({'WormBaseID': f'WBGene{str(i).zfill(8)}',
                            'Group1_1': i,
                            'Group1_2': i+1, 
                            'Group2_1': i+10,
                            'Group2_2': i+13,
        })
    outdf = pd.DataFrame().from_dict(for_outdf)
    return dcc.send_data_frame(outdf.to_excel, example_filename, sheet_name="data", index=False)


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
    Output('result-filename-modal', 'is_open'),
    [ Input('download-result-btn',"n_clicks"),
    Input("result-filename-download", "n_clicks")],
    [ State("result-filename-modal", "is_open")],
    prevent_initial_call=True
)
def download_xlsx_filename(n1, n2, is_open):
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
        pdf_filename="protclock.pdf"
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
    eventlog = UserLogging(email=current_user.email,action="download figure protclock")
    db.session.add(eventlog)
    db.session.commit()
    return dcc.send_bytes(write_image, pdf_filename)


@dashapp.callback(
    Output('download-result', 'data'),
    Input('result-filename-download',"n_clicks"),
    #Input('download-result-btn',"n_clicks"),
    State('outdf_', 'data'),
    State("result-filename", "value"),
    State("result-filename-modal", 'is_open'),
    prevent_initial_call=True
)
def download_csv(n_clicks, outdf, csv_filename, is_open):
    if n_clicks is None or n_clicks == 0:
        return

    if not csv_filename:
        csv_filename="pseudoage.xlsx"
    csv_filename=secure_filename(csv_filename)
    if csv_filename.split(".")[-1] != "xlsx":
        csv_filename=f'{csv_filename}.xlsx'

    eventlog = UserLogging(email=current_user.email,action="download csv results")
    db.session.add(eventlog)
    db.session.commit()

    outdf = pd.read_json(outdf, orient='split')

    return dcc.send_data_frame(outdf.to_excel, csv_filename, sheet_name="data", index=False)


@dashapp.callback(
    Output("redirect-violin", 'children'),
    Input("btn-violin-age", "n_clicks"),
    Input('outdf_', 'data'),
    prevent_initial_call=True,
)
def pseudoage_to_violin(n_clicks, outdf):
    if not n_clicks:
        raise PreventUpdate

    from datetime import datetime
    from time import sleep

    # Filter data
    outdf = pd.read_json(outdf, orient='split')
    violin_df = outdf[["condition", "PseudoAge"]].dropna()

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

        ask_for_help(tb_str,current_user, "protclock", session_data)

        return closed, toast, clicks
    else:
        
        raise PreventUpdate


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