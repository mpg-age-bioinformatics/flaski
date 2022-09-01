from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
from pyflaski.scatterplot import make_figure, figure_defaults
from myapp.routes.apps._utils import check_access, make_options, GROUPS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import traceback
import json
import pandas as pd
import time
import base64
import plotly.express as px
# from plotly.io import write_image
import plotly.graph_objects as go
from werkzeug.utils import secure_filename
from myapp import db
from myapp.models import UserLogging
from time import sleep

PYFLASKI_VERSION=os.environ['PYFLASKI_VERSION']
PYFLASKI_VERSION=str(PYFLASKI_VERSION)
FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("crispr",url_base_pathname=f'{PAGE_PREFIX}/crispr/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
    header_access, msg_access = check_access( 'crispr' )
    if header_access :
        return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    # if "crispr" in PRIVATE_ROUTES :
    #     appdb=PrivateRoutes.query.filter_by(route="crispr").first()
    #     if not appdb:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     allowed_users=appdb.users
    #     if not allowed_users:
    #         return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    #     if current_user.id not in allowed_users :
    #         allowed_domains=appdb.users_domains
    #         if current_user.domain not in allowed_domains:
    #             return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    eventlog = UserLogging(email=current_user.email, action="visit crispr")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("CRISPR",current_user),
            html.Div(id="app-content"),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

def make_ed_table(field_id, columns=None , df=None):
    if  type(df) != type( pd.DataFrame() ):
        df=pd.DataFrame( columns=columns )
    df=make_table(df,field_id)
    df.editable=True
    df.row_deletable=True
    df.style_cell=style_cell
    df.style_table["height"]="62vh"
    return df

def make_df_from_rows(rows):
    rows_=[]
    for row in rows:
        row=[ row[k] for k in list(row.keys()) ]
        rows_.append(row)
    df=pd.DataFrame(rows_,columns=list(rows[0].keys()))
    # df=pd.DataFrame(rows)
    # for row in rows:
    #     # print("!!!", row)
    #     df_=pd.DataFrame(row,index=[0])
    #     df=pd.concat([df,df_])
    df.reset_index(inplace=True, drop=True)
    df=df.to_json()
    return df

# Read in users input and generate submission file.
def generate_submission_file(samplenames, \
    samples, \
    library, \
    email, \
    group,\
    experiment_name,\
    folder,\
    md5sums,\
    cnv_line,\
    upstreamseq,\
    sgRNA_size,\
    efficiency_matrix,\
    SSC_sgRNA_size,\
    gmt_file,\
    mageck_test_remove_zero,\
    mageck_test_remove_zero_threshold,\
    species,\
    assembly,\
    use_bowtie,\
    depmap,\
    depmap_cell_line,\
    BAGEL_ESSENTIAL,\
    BAGEL_NONESSENTIAL,\
    mageckflute_organism ):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(
        samplenames, \
        samples, \
        library, \
        email, \
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism 
        ):
        samplenames_df=make_df_from_rows(samplenames)
        samples_df=make_df_from_rows(samples)
        library_df=make_df_from_rows(library)

        df_=pd.DataFrame({
            "Field":[
                "email", \
                "group",\
                "experiment_name",\
                "folder",\
                "md5sums",\
                "cnv_line",\
                "upstreamseq",\
                "sgRNA_size",\
                "efficiency_matrix",\
                "SSC_sgRNA_size",\
                "gmt_file",\
                "mageck_test_remove_zero",\
                "mageck_test_remove_zero_threshold",\
                "species",\
                "assembly",\
                "use_bowtie",\
                "depmap",\
                "depmap_cell_line",\
                "BAGEL_ESSENTIAL",\
                "BAGEL_NONESSENTIAL",\
                "mageckflute_organism "
                ],\
            "Value":[
                email, \
                group,\
                experiment_name,\
                folder,\
                md5sums,\
                cnv_line,\
                upstreamseq,\
                sgRNA_size,\
                efficiency_matrix,\
                SSC_sgRNA_size,\
                gmt_file,\
                mageck_test_remove_zero,\
                mageck_test_remove_zero_threshold,\
                species,\
                assembly,\
                use_bowtie,\
                depmap,\
                depmap_cell_line,\
                BAGEL_ESSENTIAL,\
                BAGEL_NONESSENTIAL,\
                mageckflute_organism 
                ]
             }, index=list(range(21)))

        df_=df_.to_json()
     
        filename=make_submission_file(".crispr.xlsx")


        return {"filename": filename, "sampleNames":samplenames_df, "samples":samples_df, "library":library_df, "crispr":df_}
    return _generate_submission_file(
        samplenames, \
        samples, \
        library, \
        email, \
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism 
    )

@dashapp.callback( 
    Output('app-content', 'children'),
    Input('url', 'pathname'))
def make_app_content(pathname):

    samplenames=make_ed_table('adding-rows-samplenames', columns=["Files","Name"] )
    samples=make_ed_table('adding-rows-samples', columns=["Label","Pairness (paired or unpaired)",\
        "List of treated samples","List of control sgRNAs",\
        "List of control genes" ] )
    librarydf=make_ed_table(  'adding-rows-library', columns=["gene_id","UID","seq","annotation"])

    groups_=make_options(GROUPS)
    groups_val="CRISPR_Screening"

    species=make_options(["homo_sapiens"])
    species_value="homo_sapiens"

    assembly=make_options(["hg19"])
    assembly_value="hg19"

    TRUE_FALSE=make_options(["TRUE","FALSE"])

    mageckflute_organism=make_options(["hsa"])


    arguments=[
        dbc.Row( 
            [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='group', options=groups_, value=groups_val, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Experiment name') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='experiment_name', placeholder="PinAPL-py_demo", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Name of your choice'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Folder') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='folder', placeholder="my_proj_folder", type='text', style={ "width":"100%" } ) ,md=3 ),
                dbc.Col( html.Label('Folder containing your files'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('md5sums') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='md5sums', placeholder="md5sums.file.txt", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('File with md5sums'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('CNV line') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='cnv_line', placeholder="T98G_CENTRAL_NERVOUS_SYSTEM", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('CNV line to take as reference'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Upstream sequence') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='upstreamseq',placeholder="TCTTGTGGAAAGGACGAAACNNNN", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Upstream sequence'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('sgRNA size') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='sgRNA_size', placeholder="20", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('sgRNA size'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Efficiency matrix') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='efficiency_matrix', placeholder="human_CRISPRi_20bp.matrix", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Eff. matrix'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('SSC sgRNA size') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='SSC_sgRNA_size', placeholder="20", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('SSC sgRNA size'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('GMT file') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='gmt_file', placeholder="msigdb.v7.2.symbols.gmt_", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('GMT file'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Mageck test remove zero') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='mageck_test_remove_zero', value="both", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Remove zeros'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Zero threshold') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='mageck_test_remove_zero_threshold', value="0", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Zero value'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Species') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='species', options=species, value=species_value, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Species'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Assembly') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='assembly', options=assembly, value=assembly_value, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Organism assembly'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bowtie') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='use_bowtie', options=TRUE_FALSE, value="FALSE", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Use Bowtie to map reads'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Depmap') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='depmap', options=TRUE_FALSE, value="FALSE", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Use Depmap as reference'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Depmap cell line') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='depmap_cell_line', type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Compare to specific Depmap cell line'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bagel essential') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='BAGEL_ESSENTIAL', value="/bagel/CEGv2.txt", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Bagel essential genes list'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Bagel essential') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='BAGEL_NONESSENTIAL', value="/bagel/NEGv1.txt", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Bagel non essential genes list'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('Mageckflute organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='mageckflute_organism', options=mageckflute_organism, value="hsa", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Mageckflute reference organism'),md=3  ), 
            ], 
            style={"margin-top":10}
        ),
    ]

    card=[
        dbc.Card( 
            [
                html.Div(
                    dcc.Upload(
                        id='upload-data',
                        children=dcc.Loading(
                            id=f"data-load",
                            type="default",
                            children=html.Div(
                                [ html.A('upload a file or fill up the form',id='upload-data-text') ],
                                style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
                            ),
                        ),               

                        style={
                            'width': '100%',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            "margin-bottom": "5px",
                            "margin-top": "5px",
                        },
                        multiple=False,
                    ),
                ),
                dcc.Tabs(
                    [
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    samplenames,
                                    id="updatable-samplenames"
                                ),
                                html.Button('Add Row', id='editing-rows-samplenames-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Sample Names", id="tab-samplenames"
                        ),
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    samples,
                                    id="updatable-samples"
                                ),
                                html.Button('Add Row', id='editing-rows-samples-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Samples", id="tab-samples"
                        ),
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    librarydf,
                                    id="updatable-library"
                                ),
                                html.Button('Add Row', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Library", id="tab-library",
                        ),
                        dcc.Tab( arguments ,label="Info", id="tab-info" ) ,
                    ]
                )
                    

            ],
            body=True,
            style={"min-width":"372px","width":"100%","margin-bottom":"2px","margin-top":"2px","padding":"0px"}#,'display': 'block'}#,"max-width":"375px","min-width":"375px"}"display":"inline-block"
        ),
        dbc.Button(
            'Submit',
            id='submit-button-state', 
            color="secondary",
            n_clicks=0, 
            style={"max-width":"372px","width":"200px","margin-top":"8px", "margin-left":"4px","margin-bottom":"50px"}#,"max-width":"375px","min-width":"375px"}
        ),  
        dbc.Modal(
            dcc.Loading(
                id=f"modal-load",
                type="default",
                children=
                    [
                        dbc.ModalHeader(dbc.ModalTitle("Whoopss..",id="modal_header") ),
                        dbc.ModalBody("something went wrong!", id="modal_body"),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="close", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
            ),
            id="modal",
            is_open=False,
        )
    ]

    app_content=html.Div(
        [
            dcc.Store( id='session-data' ),
            # dcc.Store( id='json-import' ),
            dcc.Store( id='update_labels_field-import'),
            dcc.Store( id='generate_markers-import'),
            dbc.Row( 
                [
                    dbc.Col(
                        card,
                        sm=12,md=12,lg=12,xl=12,
                        align="top",
                        style={"padding":"0px","overflow":"scroll"},
                    ),
                    # dbc.Col(
                    #     [
                    #         dcc.Loading(id="loading-stored-file", children= html.Div(id='stored-file'), style={"height":"100%"}),
                    #         dcc.Loading(
                    #             id="loading-fig-output",
                    #             type="default",
                    #             children=[
                    #                 html.Div(id="fig-output"),
                    #                 html.Div( 
                    #                     [
                    #                         dbc.Button(
                    #                             html.Span(
                    #                                 [ 
                    #                                     html.I(className="fas fas fa-file-pdf"),
                    #                                     " PDF" 
                    #                                 ]
                    #                             ),
                    #                             id='download-pdf-btn', 
                    #                             style={"max-width":"150px","width":"100%"},
                    #                             color="secondary"
                    #                         ),
                    #                         dcc.Download(id="download-pdf")
                    #                     ],
                    #                     id="download-pdf-div",
                    #                     style={"max-width":"150px","width":"100%","margin":"4px", 'display': 'none'} # 'none' / 'inline-block'
                    #                 )
                    #             ],
                    #             style={"height":"100%"}
                    #         ),
                    #         html.Div(
                    #             [
                    #                 html.Div( id="toast-read_input_file"  ),
                    #                 dcc.Store( id={ "type":"traceback", "index":"read_input_file" }), 
                    #                 html.Div( id="toast-update_labels_field"  ),
                    #                 dcc.Store( id={ "type":"traceback", "index":"update_labels_field" }), 
                    #                 html.Div( id="toast-generate_markers" ),
                    #                 dcc.Store( id={ "type":"traceback", "index":"generate_markers" }), 
                    #                 html.Div( id="toast-make_fig_output" ),
                    #                 dcc.Store( id={ "type":"traceback", "index":"make_fig_output" }), 
                    #                 html.Div(id="toast-email"),  
                    #             ],
                    #             style={"position": "fixed", "top": 66, "right": 10, "width": 350}
                    #         ),
                    #     ],
                    #     id="col-fig-output",
                    #     sm=12,md=6,lg=7,xl=8,
                    #     align="top",
                    #     style={"height":"100%"}
                    # ),

                    # dbc.Modal(
                    #     [
                    #         dbc.ModalHeader("File name"), # dbc.ModalTitle(
                    #         dbc.ModalBody(
                    #             [
                    #                 dcc.Input(id='pdf-filename', value="scatterplot.pdf", type='text', style={"width":"100%"})
                    #             ]
                    #         ),
                    #         dbc.ModalFooter(
                    #             dbc.Button(
                    #                 "Download", id="pdf-filename-download", className="ms-auto", n_clicks=0
                    #             )
                    #         ),
                    #     ],
                    #     id="pdf-filename-modal",
                    #     is_open=False,
                    # ),

                    # dbc.Modal(
                    #     [
                    #         dbc.ModalHeader("File name"), 
                    #         dbc.ModalBody(
                    #             [
                    #                 dcc.Input(id='export-filename', value="scatterplot.json", type='text', style={"width":"100%"})
                    #             ]
                    #         ),
                    #         dbc.ModalFooter(
                    #             dbc.Button(
                    #                 "Download", id="export-filename-download", className="ms-auto", n_clicks=0
                    #             )
                    #         ),
                    #     ],
                    #     id="export-filename-modal",
                    #     is_open=False,
                    # )
                ],
            align="start",
            justify="left",
            className="g-0",
            style={"height":"100%","width":"100%","overflow":"scroll"} #"86vh" "64vh"
            ),
        ]
    )
    return app_content


###
### Work from here on:
###

fields = [     
    "email", \
    "group",\
    "experiment_name",\
    "folder",\
    "md5sums",\
    "cnv_line",\
    "upstreamseq",\
    "sgRNA_size",\
    "efficiency_matrix",\
    "SSC_sgRNA_size",\
    "gmt_file",\
    "mageck_test_remove_zero",\
    "mageck_test_remove_zero_threshold",\
    "species",\
    "assembly",\
    "use_bowtie",\
    "depmap",\
    "depmap_cell_line",\
    "BAGEL_ESSENTIAL",\
    "BAGEL_NONESSENTIAL",\
    "mageckflute_organism"
]

outputs = [ Output(o, 'value') for o in fields ]

@dashapp.callback( 
    [ Output('upload-data-text', 'children'), 
    Output("updatable-samplenames", 'children'),
    Output("updatable-samples", 'children'),
    Output("updatable-library", 'children') 
    ] + outputs ,
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified'),
    prevent_initial_call=True)
def read_file(contents,filename,last_modified):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    extension=filename.split(".")[-1]
    if extension not in ['xls', "xlsx"] :
        raise dash.exceptions.PreventUpdate
    exc=pd.ExcelFile(io.BytesIO(decoded))

    if "sampleNames" in exc.sheet_names :
        samplenames=pd.read_excel(io.BytesIO(decoded), sheet_name="sampleNames")
        samplenames=make_ed_table('adding-rows-samplenames', df=samplenames )
    else:
        samplenames= dash.no_update

    if "samples" in exc.sheet_names :
        samples=pd.read_excel(io.BytesIO(decoded), sheet_name="samples")
        samples=make_ed_table('adding-rows-samples', df=samples )
    else:
        samples=dash.no_update

    if "library" in exc.sheet_names :
        library=pd.read_excel(io.BytesIO(decoded), sheet_name="library")
        library=make_ed_table('adding-rows-library', df=library )
    else:
        library=dash.no_update
    
    if "crispr" not in exc.sheet_names :
        arguments=[ dash.no_update for f in fields ]
    else:
        arguments_df=pd.read_excel(io.BytesIO(decoded), sheet_name="crispr")
        arguments_list=arguments_df["Field"].tolist()
        arguments=[]
        for f in fields :
            if f in arguments_list :
                val= arguments_df[arguments_df["Field"]==f]["Value"].tolist()[0]
                arguments.append(val)
            else:
                arguments.append( dash.no_update )
            
    return [ filename ] + [ samplenames, samples, library ] +  arguments 


states=[ State(f, 'value') for f in fields ]

# # main submission call
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    # Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    [ State("adding-rows-samplenames", 'data'),
    State("adding-rows-samples", 'data'),
    State("adding-rows-library", 'data') 
    ]+states,
    prevent_initial_call=True )
def update_output(n_clicks, \
        samplenames, \
        samples, \
        library, \
        email, \
        group,\
        experiment_name,\
        folder,\
        md5sums,\
        cnv_line,\
        upstreamseq,\
        sgRNA_size,\
        efficiency_matrix,\
        SSC_sgRNA_size,\
        gmt_file,\
        mageck_test_remove_zero,\
        mageck_test_remove_zero_threshold,\
        species,\
        assembly,\
        use_bowtie,\
        depmap,\
        depmap_cell_line,\
        BAGEL_ESSENTIAL,\
        BAGEL_NONESSENTIAL,\
        mageckflute_organism ):
    # header, msg = check_access( 'rnaseq' )
    # header, msg = None, None # for local debugging 
    # if msg :
    #     return header, msg
    # if not wget:
    #     wget="NONE"

    try:

        subdic=generate_submission_file( samplenames, \
            samples, \
            library, \
            email, \
            group,\
            experiment_name,\
            folder,\
            md5sums,\
            cnv_line,\
            upstreamseq,\
            sgRNA_size,\
            efficiency_matrix,\
            SSC_sgRNA_size,\
            gmt_file,\
            mageck_test_remove_zero,\
            mageck_test_remove_zero_threshold,\
            species,\
            assembly,\
            use_bowtie,\
            depmap,\
            depmap_cell_line,\
            BAGEL_ESSENTIAL,\
            BAGEL_NONESSENTIAL,\
            mageckflute_organism )

        # samples=pd.read_json(subdic["samples"])
        # metadata=pd.read_json(subdic["metadata"])

        # validation=validate_metadata(metadata)
        # if validation:
        #     header="Attention"
        #     return header, validation

        if os.path.isfile(subdic["filename"]):
            header="Attention"
            msg='''You have already submitted this data. Re-submission will not take place.'''
            return header, msg
        else:
            header="Success!"
            msg='''Please check your email for confirmation.'''
        

        user_domain=current_user.email
        # user_domain=user_domain.split("@")[-1]
        # mps_domain="mpg.de"
        # if user_domain[-len(mps_domain):] == mps_domain :
        # if user_domain !="age.mpg.de" :
            # subdic["filename"]=subdic["filename"].replace("/submissions/", "/submissions_ftp/")

        sampleNames=pd.read_json(subdic["sampleNames"])
        samples=pd.read_json(subdic["samples"])
        library=pd.read_json(subdic["library"])
        arguments=pd.read_json(subdic["crispr"])

        EXCout=pd.ExcelWriter(subdic["filename"])
        sampleNames.to_excel(EXCout,"sampleNames",index=None)
        samples.to_excel(EXCout,"samples",index=None)
        library.to_excel(EXCout,"library",index=None)
        arguments.to_excel(EXCout,"crispr",index=None)
        EXCout.save()

        # if user_domain == "age.mpg.de" :
        send_submission_email(user=current_user, submission_type="crispr", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])
        # else:
        #     send_submission_ftp_email(user=current_user, submission_type="RNAseq", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])
    except:
        header=dash.no_update
        msg=dash.no_update

    return header, msg

@dashapp.callback(
    Output('adding-rows-samplenames', 'data'),
    Input('editing-rows-samplenames-button', 'n_clicks'),
    State('adding-rows-samplenames', 'data'),
    State('adding-rows-samplenames', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output('adding-rows-samples', 'data'),
    Input('editing-rows-samples-button', 'n_clicks'),
    State('adding-rows-samples', 'data'),
    State('adding-rows-samples', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output('adding-rows-library', 'data'),
    Input('editing-rows-library-button', 'n_clicks'),
    State('adding-rows-library', 'data'),
    State('adding-rows-library', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output("modal", "is_open"),
    [Input("submit-button-state", "n_clicks"), Input("close", "n_clicks")],
    [State("modal", "is_open")],
)
def toggle_modal(n1, n2, is_open):
    if n1 or n2:
        return not is_open
    return is_open

@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open