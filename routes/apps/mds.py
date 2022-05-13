from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from myapp.models import UserLogging
#from flaski.routines import check_session_app
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, make_table, encode_session_app
from pyflaski.mds import make_figure, figure_defaults
from pyflaski.scatterplot import figure_defaults as scatter_pa
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
from time import sleep


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("mds",url_base_pathname=f'{PAGE_PREFIX}/mds/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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

def run_mds_and_cache(df, pa, cache):
    @cache.memoize(timeout=3600)
    def _run_mds_and_cache(df, pa, cache):
        projected = make_figure(df,pa)
        mds_results={ "projected": projected.to_json() }
        return mds_results
    return _run_mds_and_cache(df, pa, cache)


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
    eventlog = UserLogging(email=current_user.email, action="visit mds")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("MDS",current_user),
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
                ############################
                dbc.Row(
                    [
                        dbc.Label("Row Names",width = 4),
                        dbc.Col(                        
                            dcc.Dropdown( placeholder="index", id='xvals', multi=False),
                            width=8
                        ),
                    ],
                    className="g-1",
                ),
                ############################
                html.Div(id="group-section"),
                ############################
                dbc.Row(
                    [
                        dbc.Label("Data Columns",width = 4),
                        dbc.Col(                        
                            dcc.Dropdown( placeholder="data columns", id='yvals', multi=True),
                            width=8
                        ),
                    ],
                    className="g-1",
                ),
                ############################
                dbc.Card(
                    [
                        dbc.CardHeader(
                            html.H2(
                                dbc.Button( "Scaling", color="black", id={'type':"dynamic-card","index":"scaling"}, n_clicks=0,style={ "margin-bottom":"5px","width":"100%"}),
                            ),
                            style={ "height":"40px","padding":"0px"}
                        ),
                        dbc.Collapse(
                            dbc.CardBody(
                                [
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Number of dimensions:",html_for="ncomponents", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=8
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["ncomponents"], id='ncomponents',style=card_input_style),
                                        width=4
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Top % most variable rows:",html_for="percvar", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=8
                                    ),
                                    dbc.Col(
                                        dcc.Input(value=pa["percvar"], id='percvar',style=card_input_style),
                                        width=4
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ############################
                                dbc.Row(
                                    [
                                    dbc.Col(
                                        dbc.Label("Scale input data on:",html_for="scale_value", style={"margin-top":"5px"}),
                                        style={"textAlign":"left","padding-right":"2px"},
                                        width=8
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown( options=make_options(pa["scale"]), value=pa["scale_value"], id='scale_value', multi=False, clearable=False),
                                        width=4
                                    ),
                                    ],
                                    className="g-1",
                                ),
                                ######### END OF CARD #########
                                ]
                                ,style=card_body_style
                            ),
                            id={'type':"collapse-dynamic-card","index":"scaling"},
                            is_open=False,
                        ),
                    ],
                    style={"margin-top":"2px","margin-bottom":"2px"} 
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
            style={ "min-width":"372px","width":"100%", "display": "none"},
            className="g-0",    
            # style={ "margin-left":"0px" , "margin-right":"0px"}
        ),
        dbc.Button(
                    'Submit',
                    id='submit-button-state', 
                    color="secondary",
                    n_clicks=0, 
                    style={"min-width":"372px","width":"100%","margin-top":"2px","margin-bottom":"2px"}#,"max-width":"375px","min-width":"375px"}
                )
    ]

    app_content=html.Div(
        [
            dcc.Store( id='session-data' ),
            # dcc.Store( id='json-import' ),
            dcc.Store( id='update_group_field-import'),
            dcc.Store( id='update_labels_field-import'),
            dcc.Store( id='generate_markers-import'),
            dbc.Row( 
                [
                    dbc.Col(
                        side_bar,
                        sm=12,md=6,lg=5,xl=4,
                        align="top",
                        style={"padding":"0px","overflow":"scroll"},
                    ),
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-fig-output",
                                type="default",
                                children=[
                                    html.Div(id="fig-output", style={"margin-left": "5px"}),
                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results (xlsx)" 
                                                    ]
                                                ),
                                                id='save-excel-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='save-excel')
                                        ],
                                        id="save-excel-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),                                    
                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-lg fa-save"),
                                                        " Results (tsv)" 
                                                    ]
                                                ),
                                                id='save-tsv-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='save-tsv')
                                        ],
                                        id="save-tsv-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),
                                    html.Div( 
                                        [
                                            dbc.Button(
                                                html.Span(
                                                    [ 
                                                        html.I(className="far fa-chart-bar"),
                                                        " Scatterplot" 
                                                    ]
                                                ),
                                                id='scatterplot-session-btn', 
                                                style={"max-width":"150px","width":"100%"},
                                                color="secondary"
                                            ),
                                            dcc.Download(id='scatterplot-session')
                                        ],
                                        id="scatterplot-session-div",
                                        style={"max-width":"150px","width":"100%","margin":"4px", 'display':'none'} # 'none' / 'inline-block'
                                    ),
                                ],
                                style={"height":"100%"}
                            ),
                            html.Div(
                                [
                                    html.Div( id="toast-read_input_file"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"read_input_file" }), 
                                    html.Div( id="toast-update_group_field"  ),
                                    dcc.Store( id={ "type":"traceback", "index":"update_group_field" }), 
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

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), # dbc.ModalTitle(
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='excel-filename', value="mds.xlsx", type='text', style={"width":"100%"})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Download", id="excel-filename-download", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="excel-filename-modal",
                        is_open=False,
                    ),

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), # dbc.ModalTitle(
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='tsv-filename', value="mds.tsv", type='text', style={"width":"100%"})
                                ]
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Download", id="tsv-filename-download", className="ms-auto", n_clicks=0
                                )
                            ),
                        ],
                        id="tsv-filename-modal",
                        is_open=False,
                    ),

                    dbc.Modal(
                        [
                            dbc.ModalHeader("File name"), 
                            dbc.ModalBody(
                                [
                                    dcc.Input(id='export-filename', value="mds.json", type='text', style={"width":"100%"})
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
                    )
                ],
            align="start",
            justify="left",
            className="g-0",
            style={"height":"86vh","width":"100%","overflow":"scroll"}
            ),
        ]
    )
    return app_content

# example reading session from server storage
@dashapp.callback( 
    Output('upload-data', 'contents'),
    Output('upload-data', 'filename'),
    Output('upload-data', 'last_modified'),
    Input('session-id', 'data'))
def read_session_redis(session_id):
    if "session_data" in list( session.keys() )  :
        imp=session["session_data"]
        del(session["session_data"])
        sleep(3)
        return imp["session_import"], imp["sessionfilename"], imp["last_modified"]
    else:
        return dash.no_update, dash.no_update, dash.no_update
   

read_input_updates=[
    "groups",
    "ncomponents",
    "percvar",
    "scale_value"    
]

read_input_updates_outputs=[ Output(s, 'value') for s in read_input_updates ]

@dashapp.callback( 
    [Output('xvals', 'options'),
    Output('yvals', 'options'),
    Output('upload-data','children'),
    Output('toast-read_input_file','children'),
    Output({ "type":"traceback", "index":"read_input_file" },'data'),
    # Output("json-import",'data'),
    Output('xvals', 'value'),
    Output('yvals', 'value')] + read_input_updates_outputs ,
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('session-id', 'data'),
    prevent_initial_call=True)
def read_input_file(contents,filename,last_modified,session_id):
    if not filename :
        raise dash.exceptions.PreventUpdate

    pa_outputs=[ dash.no_update for k in  read_input_updates ]
    try:
        if filename.split(".")[-1] == "json":
            app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "mds")
            df=pd.read_json(app_data["df"])
            cols=df.columns.tolist()
            cols_=make_options(cols)
            filename=app_data["filename"]
            xvals=app_data['pa']["xvals"]
            yvals=app_data['pa']["yvals"]

            pa=app_data["pa"]

            pa_outputs=[pa[k] for k in  read_input_updates ]

        else:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"mds")
            app_data=dash.no_update
            cols=df.columns.tolist()
            cols_=make_options(cols)
            xvals=cols[0]
            yvals=cols[1:len(cols)]

        upload_text=html.Div(
            [ html.A(filename, id='upload-data-text') ],
            style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
        )     
        return [cols_, cols_, upload_text, None, None,  xvals, yvals] + pa_outputs

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem reading your input file:","read_input_file", e, current_user,"mds")
        return [dash.no_update, dash.no_update, dash.no_update, toast, tb_str, dash.no_update, dash.no_update ] + pa_outputs


@dashapp.callback( 
    Output('group-section', 'children'),
    Output('toast-update_group_field','children'),
    Output({ "type":"traceback", "index":"update_group_field" },'data'),
    Output('update_group_field-import', 'data'),
    Input('session-id','data'),
    Input('xvals','value'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('update_group_field-import', 'data'),
)
def update_group_field(session_id,col,contents,filename,last_modified,update_group_field_import):
    try:
        if filename:
            df=parse_table(contents,filename,last_modified,current_user.id,cache,"mds")
            if col:
                group=df[[col]].drop_duplicates()[col].tolist()
                group_=make_options(group)
            else:
                group=df.index.tolist()
                group_=make_options(group)

            if ( filename.split(".")[-1] == "json" ) and ( not update_group_field_import ) :
                app_data=parse_import_json(contents,filename,last_modified,current_user.id,cache, "mds")

                groups=app_data['pa']["groups"]
                update_group_field_import=True
            else:
                groups=[]


            group_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Groups (in Row)", width=4),
                        dbc.Col(
                            dcc.Dropdown( options=group_, value=None, id='groups', multi=False),
                            width=8
                        )
                    ],
                    className="g-1",
                    style={"margin-top":"2px"}
                )
            )
        else:
            group_section=dbc.Form(
                dbc.Row(
                    [
                        dbc.Label("Groups (in Row)", width=4),
                        dbc.Col(
                            dcc.Dropdown( placeholder="group", id='groups', multi=False),
                            width=8
                        )
                    ],
                    # row=True,
                    className="g-1",
                    style= {'display': 'none',"margin-top":"2px"}
                )
            )

        return group_section, None, None, update_group_field_import
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem updating the group field.","update_group_field", e, current_user,"cellplot")
        return dash.no_update, toast, tb_str, dash.no_update


states=[
    State('xvals', 'value'),
    State('groups', 'value'),
    State('yvals', 'value'),
    State('ncomponents', 'value'),
    State('percvar', 'value'),
    State('scale_value', 'value'),
]

@dashapp.callback( 
    Output('fig-output', 'children'),
    Output('toast-make_fig_output','children'),
    Output('session-data','data'),
    Output({ "type":"traceback", "index":"make_fig_output" },'data'),
    Output('save-excel-div', 'style'),
    Output('save-tsv-div', 'style'),
    Output('scatterplot-session-div', 'style'),
    Output('export-session','data'),
    Output('save-excel', 'data'),
    Output('save-tsv', 'data'),
    Input("submit-button-state", "n_clicks"),
    Input("export-filename-download","n_clicks"),
    Input("save-session-btn","n_clicks"),
    Input("saveas-session-btn","n_clicks"),
    Input("excel-filename-download","n_clicks"),
    Input("tsv-filename-download","n_clicks"),
    Input("scatterplot-session-btn","n_clicks"),
    [ State('session-id', 'data'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    State('export-filename','value'),
    State('excel-filename', 'value'),
    State('tsv-filename', 'value'),
    State('upload-data-text', 'children')] + states,
    prevent_initial_call=True
    )
def make_fig_output(n_clicks,export_click,save_session_btn,saveas_session_btn,save_excel_btn, save_tsv_btn, scatterplot_session_btn, session_id,contents,filename,last_modified,export_filename,excel_filename,tsv_filename,upload_data_text, *args):
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
        input_names = [item.component_id for item in states]

        df=parse_table(contents,filename,last_modified,current_user.id,cache,"mds")

        pa=figure_defaults()
        for k, a in zip(input_names,args) :
            if type(k) != dict :
                pa[k]=a
            elif type(k) == dict :
                k_=k['type'] 
                for i, a_ in enumerate(a) :
                    pa[k_]=a_

        session_data={ "session_data": {"app": { "mds": {'last_modified':last_modified,"pa":pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        
    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem parsing your input.","make_fig_output", e, current_user,"mds")
        return dash.no_update, toast, None, tb_str, download_buttons_style_hide, download_buttons_style_hide,download_buttons_style_hide, None, None, None

    if button_id == "export-filename-download" :
        if not export_filename:
            export_filename="mds.json"
        export_filename=secure_filename(export_filename)
        if export_filename.split(".")[-1] != "json":
            export_filename=f'{export_filename}.json'  

        def write_json(export_filename,session_data=session_data):
            export_filename.write(json.dumps(session_data).encode())
            # export_filename.seek(0)

        return dash.no_update, None, None, None, dash.no_update, dash.no_update,dash.no_update, dcc.send_bytes(write_json, export_filename), None, None

    if button_id == "save-session-btn" :
        try:
            if filename and filename.split(".")[-1] == "json" :
                toast=save_session(session_data, filename,current_user, "make_fig_output" )
                return dash.no_update, toast, None, None, dash.no_update,dash.no_update,dash.no_update, None, None, None
            else:
                session["session_data"]=session_data
                return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'), dash.no_update, dash.no_update, dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update
                # save session_data to redis session
                # redirect to as a save as to file server

        except Exception as e:
            tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
            toast=make_except_toast("There was a problem saving your file.","save", e, current_user,"mds")
            return dash.no_update, toast, None, tb_str, dash.no_update, dash.no_update,dash.no_update, None, None, None

        # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)

    if button_id == "saveas-session-btn" :
        session["session_data"]=session_data
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/saveas/", id='index'),  dash.no_update,  dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,dash.no_update, dash.no_update
          # return dash.no_update, None, None, None, dash.no_update, dcc.send_bytes(write_json, export_filename)
    
    if button_id == "excel-filename-download":
        if not excel_filename:
            excel_filename=secure_filename("mds_results.%s.xlsx" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        excel_filename=secure_filename(excel_filename)
        if excel_filename.split(".")[-1] != "xlsx":
            excel_filename=f'{excel_filename}.xlsx'  

        mds_results=run_mds_and_cache(df, pa, cache)
        projected = pd.read_json(mds_results["projected"]) 

        import io
        output = io.BytesIO()
        writer= pd.ExcelWriter(output)
        projected.to_excel(writer, sheet_name = 'mds results', index = False)
        writer.save()
        data=output.getvalue()
        return dash.no_update, None, None, None, dash.no_update, dash.no_update,dash.no_update, None, dcc.send_bytes(data, excel_filename), None

    if button_id == "tsv-filename-download":
        if not tsv_filename:
            tsv_filename=secure_filename("mds_results.%s.tsv" %(time.strftime("%Y%m%d_%H%M%S", time.localtime())))
        tsv_filename=secure_filename(tsv_filename)
        if tsv_filename.split(".")[-1] != "tsv":
            tsv_filename=f'{tsv_filename}.tsv'  

        mds_results=run_mds_and_cache(df, pa, cache)
        projected = pd.read_json(mds_results["projected"]) 

        return dash.no_update, None, None, None,dash.no_update, dash.no_update, dash.no_update, None, None, dcc.send_data_frame(projected.to_csv, tsv_filename, sep = "\t")


    if button_id == "scatterplot-session-btn":
        mds_results=run_mds_and_cache(df, pa, cache)
        projected = pd.read_json(mds_results["projected"])
        
        sp_pa=scatter_pa()

        sp_pa["fig_width"] = "600"
        sp_pa["fig_height"] = "600"
        sp_pa["xvals"] = "Component1"
        sp_pa["yvals"] = "Component2"
        sp_pa["labels_col_value"] = "Sample"
        sp_pa["title"] = "MDS"
        sp_pa["xlabel"] = "Component1"
        sp_pa["ylabel"] = "Component2"
        
        session_data={ "session_data": {"app": { "scatterplot": {"filename":"<from MDS app>.json" ,'last_modified':last_modified,"df":mds_results["projected"],"pa":sp_pa} } } }
        session_data["APP_VERSION"]=app.config['APP_VERSION']
        session_data=encode_session_app(session_data)
        session["session_data"]=session_data
        #return  dash.no_update, None, None, None, dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update, None, None, None
        return  dcc.Location(pathname=f'{PAGE_PREFIX}/scatterplot/', id="index"), None, None, None,  dash.no_update,dash.no_update,dash.no_update, None, None, None

    try:
        fig=None
        mds_results=run_mds_and_cache(df, pa, cache)
        projected = pd.read_json(mds_results["projected"]) 
        # truncate to two decimal points were appropriate

        # print(df.columns.tolist())
        # df["%"]=df["%"].apply( lambda x: round(x, 2) )
        # table_headers=projected.columns.tolist()
        # for col in ["%","Fold Enrichment"]:
        #     df[col]=df[col].apply(lambda x: "{0:.2f}".format(float(x)))
        # for col in ["PValue","Bonferroni","Benjamini","FDR"]:
        #     df[col]=df[col].apply(lambda x: '{:.2e}'.format(float(x)))
        # # for col in ["Genes"]+table_headers[14:]:
        # #     df[col]=df[col].apply(lambda x: str(x)[:40]+"..")

        # if "Z-score" in table_headers:
        #     download_buttons_style_scatterforward={"max-width":"150px","width":"100%","margin":"4px",'display': 'inline-block'} 
        #     for col in ["Z-score", "mean log2 FC", "-log10 (pvalue)"]:
        #         df[col]=df[col].apply(lambda x: "{0:.3f}".format(float(x)))
        #     addon=16
        # else:
        #     download_buttons_style_scatterforward={"max-width":"150px","width":"100%","margin":"4px",'display': 'none'} 
        #     addon=13

        # for col in ["Genes"]+table_headers[addon:]:
        #     df[col]=df[col].apply(lambda x: str(x)[:40]+"..")

        fig=make_table(projected, "mds_results", fixed_columns = False)

        return fig, None, None, None,  download_buttons_style_show,download_buttons_style_show,download_buttons_style_show,None, None, None

    except Exception as e:
        tb_str=''.join(traceback.format_exception(None, e, e.__traceback__))
        toast=make_except_toast("There was a problem generating your output.","make_fig_output", e, current_user,"mds")
        return dash.no_update, toast, session_data, tb_str, download_buttons_style_hide,  download_buttons_style_hide, download_buttons_style_hide, None, None, None


@dashapp.callback(
    Output('excel-filename-modal', 'is_open'),
    [ Input('save-excel-btn',"n_clicks"),Input("excel-filename-download", "n_clicks")],
    [ State("excel-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_excel_filename(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output('tsv-filename-modal', 'is_open'),
    [ Input('save-tsv-btn',"n_clicks"),Input("tsv-filename-download", "n_clicks")],
    [ State("tsv-filename-modal", "is_open")], 
    prevent_initial_call=True
)
def download_tsv_filename(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

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

        ask_for_help(tb_str,current_user, "mds", session_data)

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