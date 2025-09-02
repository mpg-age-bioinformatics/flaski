from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_options, GROUPS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import base64
import pandas as pd
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("cutandtag",url_base_pathname=f'{PAGE_PREFIX}/cutandtag/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="CutNTag" , assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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

# improve tables styling
style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    eventlog = UserLogging(email=current_user.email, action="visit cutandtag")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("CutNTag",current_user),
            html.Div(id="app-content", style={"height":"100%","overflow":"scroll"}),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

# Read in users input and generate submission file.
def generate_submission_file(rows_atac, rows_input, email,group,folder,md5sums,project_title,organism,ercc,seq, adapter, genes, spikeIn,spikeIn_spec, IgG, wget, ftp):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(rows_atac, rows_input, email,group,folder,md5sums,project_title,organism,ercc,seq, adapter,genes,spikeIn,spikeIn_spec, IgG, wget, ftp):
        df=pd.DataFrame()
        for row in rows_atac:
            if row['Read 1'] != "" :
                df_=pd.DataFrame(row,index=[0])
                df=pd.concat([df,df_])
        df.reset_index(inplace=True, drop=True)

        dfi=pd.DataFrame()
        for row in rows_input:
            if row["Input Sample"] != "" :
                df_=pd.DataFrame(row,index=[0])
                dfi=pd.concat([dfi,df_])
        dfi.reset_index(inplace=True, drop=True)

        df_=pd.DataFrame({"Field":["email","Group","Folder","md5sums","Project title", "Organism", "ERCC",
                                   "seq","Adapter sequence", "genes", "spikeIn", "spikeIn spec", "IgG Control", "wget" ],\
                          "Value":[email,group,folder,md5sums,project_title, organism, ercc,\
                                    seq, adapter,genes,spikeIn,spikeIn_spec,IgG,wget]}, index=list(range(14)))
        df=df.to_json()
        dfi=dfi.to_json()
        df_=df_.to_json()
        filename=make_submission_file(".CutNTag.xlsx")

        return {"filename": filename, "samples":df, "input":dfi , "metadata":df_}
    return _generate_submission_file(rows_atac, rows_input, email,group,folder,md5sums,project_title,organism,ercc,seq,adapter,genes,spikeIn,spikeIn_spec,IgG,wget,ftp)


@dashapp.callback(
    Output('app-content', component_property='children'),
    Input('session-id', 'data')
)
def make_app_content(session_id):
    header_access, msg_access = check_access( 'cutandtag' )
    # header_access, msg_access = None, None # for local debugging 

    samples_df=pd.DataFrame( columns=["Sample","Group","Replicate","Read 1", "Read 2"] )
    samples_eg_df=pd.DataFrame( 
        { 
            "Sample":["WT_control_1", "WT_control_2",
                      "MUT_control_1", "MUT_control_2",
                      "WT_treated_1", "WT_treated_2",
                      "MUT_treated_1", "MUT_treated_2",
                      "WT_control_Input_1", "MUT_control_Input_1", 
                      "WT_treated_Input_1", "MUT_treated_Input_1"] ,
            "Group" : ['WT_control','WT_control',
                       'MUT_control','MUT_control',
                       'WT_treated','WT_treated',
                       'MUT_treated','MUT_treated',
                       'WT_control_Input','MUT_control_Input', 
                       'WT_treated_Input', 'MUT_treated_Input'] ,
            "Replicate": ['1','2','1','2','1','2','1','2','1','1','1','1'],
            "Read 1": 
                [ 
                    "A006850092_131904_S2_L002_R1_001.fastq.gz,A003450092_131904_S2_L003_R1_001.fastq.gz",
                    "A006850092_131924_S12_L002_R1_001.fastq.gz",
                    "A006850092_131944_S22_L002_R1_001.fastq.gz",
                    "A006850092_131906_S3_L002_R1_001.fastq.gz",
                    "A006850094_131926_S3_L001_R1_001.fastq.gz",
                    "A006850092_131956_S28_L002_R1_001.fastq.gz",
                    "A006850092_131904_S245_L002_R1_001.fastq.gz",
                    "A006850092_131924_S124_L002_R1_001.fastq.gz",
                    "A006850092_131944_S2245_L002_R1_001.fastq.gz",
                    "A006850092_131906_S345_L002_R1_001.fastq.gz",
                    "A006850092_131906_S348_L002_R1_001.fastq.gz",
                    "A006850092_131906_S349_L002_R1_001.fastq.gz",

                ],
            "Read 2": 
                [ 
                "A003450092_131904_S2_L002_R2_001.fastq.gz,A003450092_131904_S2_L003_R2_001.fastq.gz",
                "A006850092_131924_S12_L002_R2_001.fastq.gz",
                "A006850092_131944_S22_L002_R2_001.fastq.gz",
                "A006850092_131906_S3_L002_R2_001.fastq.gz",
                "A006850094_131926_S3_L001_R2_001.fastq.gz",
                "A006850092_131956_S28_L002_R2_001.fastq.gz",
                "A006850092_131904_S245_L002_R2_001.fastq.gz",
                "A006850092_131924_S124_L002_R2_001.fastq.gz",
                "A006850092_131944_S2245_L002_R2_001.fastq.gz",
                "A006850092_131906_S345_L002_R2_001.fastq.gz",
                "A006850092_131906_S348_L002_R2_001.fastq.gz",
                "A006850092_131906_S349_L002_R2_001.fastq.gz",

            ],
            "Notes":  
                [
                    "eg. 2 files / sample", "","","","","","","","","","",""
                ]
        }
    )

    input_df=pd.DataFrame(columns=["CutNTag Sample", "Input Sample"])
    input_eg_df=pd.DataFrame( { "CutNTag Sample" :["WT_control_1","WT_control_2","MUT_control_1","MUT_control_2","WT_treated_1","WT_treated_2","MUT_treated_1","MUT_treated_2"] ,\
                                "Input Sample" :[ "WT_control_Input_1","WT_control_Input_1","MUT_control_Input_1","MUT_control_Input_1","WT_treated_Input_1","WT_treated_Input_1", "MUT_treated_Input_1","MUT_treated_Input_1"] } )


    # generate dropdown options
    organisms=["celegans","mmusculus","hsapiens","dmelanogaster"] # "nfurzeri", "c_albicans_sc5314"
    organisms_=make_options(organisms)
    spikeIn_dropdown=make_options(["dmelanogaster", "escherichia_coli"])
    ercc_=make_options(["YES","NO"])
    # yes_no_=make_options(["yes","no"])
    seq_=make_options(["single","paired"])
    cutNtag_options=make_options(["YES","NO"])


    readme_age='''
**New data**

For submitting samples for analysis you will need to first copy your raw files into `smb://octopus/group_bit_automation`.

Make sure you create a folder eg. `my_proj_folder` and that all your `fastq.gz` files are inside as well as your md5sums file (attention: only one md5sums file per project).

All files will have to be on your project folder (eg. `my_proj_folder` in `Info` > `Folder`) do not create further subfolders.

Once all the files have been copied, edit the `Samples` and `Info` tabs here and then press submit.

**Archived data**

For analyzing previously archived data you do not need to transfer your files. For this in the `Folder` and `md5sums` fields you will need to 
type in *TAPE*.
    '''

    readme_mps='''
**Data transfer** 

Once you've submited your form you will receive instructions on how to upload your data over FTP.
    '''

    readme_common=f'''
**SRA**

If you want to analyse **GEO/SRA** data you can do this without downloading the respective files by giving in 
the SRA run number instead of the file name. If you are analysing paired end data and only one run number 
exists please give in the same run number in `Read 2`. In the `Folder` and `md5sums` fields you will need to 
type in *SRA*. An example can be found [here](https://youtu.be/KMtk3NCWVnI). 

**Samples**

Samples will be renamed to `Group_Replicate.fastq.gz` Group -- Replicate combinations should be unique or files will be overwritten.
    '''

    readme_age=f'''
{readme_age}

{readme_common}
    '''

    readme_mps=f'''
{readme_mps}

{readme_common}
    '''

    readme_noaccess='''
**You have no access to this App.** 

Once you have been given access more information will be displayed on how to transfer your raw data.
    '''


    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]

    mps_domain="mpg.de"
    #if user_domain[-len(mps_domain):] == mps_domain :
    if user_domain =="age.mpg.de" :
        readme=dcc.Markdown(readme_mps, style={"width":"90%", "margin":"10px"} )
        groups_=make_options(GROUPS)
        groups_val=None
        folder_row_style={"margin-top":10, 'display': 'none' }
        folder="FTP"
    elif not header_access :
        readme=dcc.Markdown(readme_mps, style={"width":"90%", "margin":"10px"} )
        groups_=make_options([user_domain])
        groups_val=user_domain
        folder_row_style={"margin-top":10, 'display': 'none' }
        folder="FTP"
    else:
        readme=dcc.Markdown(readme_noaccess, style={"width":"90%", "margin":"10px"} )
        groups_=make_options(["External"])
        groups_val="External"
        folder_row_style={"margin-top":10, 'display': 'none' }
        folder="FTP" 

    samples_df=make_table(samples_df,'samples-table')
    samples_df.editable=True
    samples_df.row_deletable=True
    samples_df.style_cell=style_cell
    samples_df.style_table["height"]="62vh"

    samples_eg_df=make_table(samples_eg_df,'example-table')
    samples_eg_df.style_cell=style_cell
    samples_eg_df.style_table["height"]="68vh"

    input_df=make_table(input_df,'input-table')
    input_df.editable=True
    input_df.row_deletable=True
    input_df.style_cell=style_cell
    input_df.style_table["height"]="62vh"

    input_eg_df=make_table(input_eg_df,'input-example-table')
    input_eg_df.style_cell=style_cell
    input_eg_df.style_table["height"]="68vh"


    # arguments 
    arguments=[ 
        dbc.Row( 
            [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, value=groups_val, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('Folder') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='folder', placeholder="my_proj_folder", value=folder, type='text', style={ "width":"100%" } ) ,md=3 ),
                dbc.Col( html.Label('Folder containing your files'),md=3  ), 
            ], 
            style=folder_row_style
        ),
        dbc.Row( 
            [
                dbc.Col( html.Label('md5sums') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='md5sums', placeholder="md5sums.file.txt", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('File with md5sums'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('Project title') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='project_title', placeholder="my_super_proj", value="", type='text', style={ "width":"100%"}, maxLength=32) ,md=3 ),
                dbc.Col( html.Label('Give a name to your project'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('Organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-organism', options=organisms_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('ERCC') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-ercc', options=ercc_,value="NO", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('ERCC spikeins'),md=3  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}),  
        dbc.Row( 
            [
                dbc.Col( html.Label('seq') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-seq', options=seq_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('single or paired end sequencing'),md=6  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}),  
        dbc.Row( 
            [
                dbc.Col( html.Label('Adapter sequence') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input( id='adapter', placeholder="adapter_read1.fa,adapter_read2.fa",value="none",type='text',style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('fasta file containing potential adapter sequence to trim, e.g. transposase adapter. For single end sequencing \
                                    `<filename>.fa`. For paired end sequencing `<filename1>.fa,<filename2>.fa` '),md=6  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}), 
        dbc.Row( 
            [
                dbc.Col( html.Label('Genes') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='genes', placeholder="TP53,CDKN1A", value="none", type='text', style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Comma separated list of genes for which to make coverage plots in either gene name or ensembl gene id as in https://www.ensembl.org'),md=6  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}), 
        dbc.Row( 
            [
                dbc.Col( html.Label('Spike-In') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-spikein', options=cutNtag_options, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('If spike-in DNA was used in the experimental protocol'),md=6  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('Spike-In Organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='spikeIn_spec', options=spikeIn_dropdown, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={"margin-top":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('IgG Control') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-IgG', options=cutNtag_options, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('If there are respective IgG Control samples'),md=6  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10}),
        dbc.Row( 
            [
                dbc.Col( html.Label('ftp user') ,md=3 , style={"textAlign":"right"}), 
                dbc.Col( dcc.Input(id='ftp', placeholder="ftp user name", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label("if data has already been uploaded please provide the user name used for ftp login"), md=3 ), 
            ], 
            style={ "margin-top":10, "margin-bottom":10 }),     
        dbc.Row( 
            [
                dbc.Col( html.Label('wget') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='wget', placeholder="wget -r --http-user=NGS_BGarcia_SRE01_A006850205 --http-passwd=qlATOWs0 http://bastet2.ccg.uni-koeln.de/downloads/NGS_BGarcia_SRE01_A006850205", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label("`wget` command for direct download (optional)"),md=3  ), 
            ], 
            style={"margin-top":10,"margin-bottom":10, 'display': 'none'}), 
    ]

    content = [
        dbc.Card(
            
                [
                    html.Div(
                        dcc.Upload(
                            id='upload-data',
                            children=html.Div(
                                [ html.A('upload a file or fill up the form',id='upload-data-text') ],
                                style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
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
                        dcc.Tab( readme, label="Readme", id="tab-readme") ,
                        dcc.Tab( samples_eg_df,label="Samples (example)", id="tab-samples-example") ,
                        dcc.Tab( input_eg_df,label="Input (example)", id="tab-input-example"),
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    samples_df,
                                    id="updatable-df"
                                ),
                                html.Button('Add Sample', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Samples", id="tab-samples",
                        ),

                        dcc.Tab( 
                            [ 
                                html.Div(
                                    input_df,
                                    id="updatable-df-ai"
                                ),
                                html.Button('Add Sample', id='input-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Input", id="tab-input",
                        ),


                        dcc.Tab( arguments ,label="Info", id="tab-info" ) ,
                    ]
                )
            ],
            body=False
        ),
        html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "200px","margin-top":4, "margin-bottom":"50px"}),
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
        ),
        dcc.Download( id="download-file" )
    ]
    
    return content


@dashapp.callback( 
    Output("updatable-df", 'children'),
    Output("updatable-df-ai", 'children'),
    Output('email', 'value'),
    Output('opt-group', 'value'),
    Output('folder', 'value'),
    Output('md5sums', 'value'),
    Output('project_title', 'value'),
    Output('opt-organism', 'value'),
    Output('opt-ercc', 'value'),
    Output('opt-seq', 'value'),
    Output('adapter', 'value'),
    Output('genes', 'value'),
    Output('opt-spikein', 'value'),
    Output('spikeIn_spec', 'value'),
    Output('opt-IgG', 'value'),
    Output('wget', 'value'), 
    Output('ftp', 'value'), 
    Output('upload-data-text', 'children'),
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
    if "samples" not in exc.sheet_names :
        raise dash.exceptions.PreventUpdate
    if "CutNTag" not in exc.sheet_names :
        raise dash.exceptions.PreventUpdate
    samples = pd.read_excel(io.BytesIO(decoded), sheet_name="samples")
    CutNTag = pd.read_excel(io.BytesIO(decoded), sheet_name="CutNTag")
    input = pd.read_excel(io.BytesIO(decoded), sheet_name="input")

    samples = samples[ samples.columns.tolist()[:6]]

    samples_df=make_table(samples,'samples-table')
    samples_df.editable=True
    samples_df.row_deletable=True
    samples_df.style_cell=style_cell
    samples_df.style_table["height"]="62vh"

    input_df=make_table(input,'input-table')
    input_df.editable=True
    input_df.row_deletable=True
    input_df.style_cell=style_cell
    input_df.style_table["height"]="62vh"

    values_to_return=[]
    fields_to_return=[ "email", "Group", "Folder", "md5sums", "Project title", "Organism", "ERCC", "seq", "Adapter sequence","Genes", "spikeIn", "spikeIn spec", "IgG Control", "wget", "ftp" ]
    # for f in fields_to_return:
    #     values_to_return.append(  ChIPseq[ChIPseq["Field"]==f]["Value"].tolist()[0]  )

    fields_on_file=CutNTag["Field"].tolist()

    for f in fields_to_return:
        if f in  fields_on_file:
            values_to_return.append(  CutNTag[CutNTag["Field"]==f]["Value"].tolist()[0]  )
        else:
            values_to_return.append( dash.no_update )

    return [ samples_df ] +  [ input_df ] + values_to_return + [ filename ]

# main submission call
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    Output("download-file","data"),
    # Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('samples-table', 'data'),
    State('input-table', 'data'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('folder', 'value'),
    State('md5sums', 'value'),
    State('project_title', 'value'),
    State('opt-organism', 'value'),
    State('opt-ercc', 'value'),
    State('opt-seq', 'value'),
    State('adapter', 'value'),
    State('genes', 'value'),
    State('opt-spikein', 'value'),
    State('spikeIn_spec', 'value'),
    State('opt-IgG', 'value'),
    State('wget', 'value'),
    State('ftp', 'value'),
    prevent_initial_call=True )
def update_output(n_clicks,rows_atac,rows_input,email,group,folder,md5sums,project_title,organism,ercc,seq, adapter,genes,spikeIn,spikeIn_spec,IgG, wget, ftp ):
    header, msg = check_access( 'cutandtag' )
    # header, msg = None, None # for local debugging 
    if msg :
        return header, msg, dash.no_update

    if not wget:
        wget="NONE"
    subdic=generate_submission_file(rows_atac,rows_input,email,group,folder,md5sums,project_title,organism,ercc,seq,adapter,genes,spikeIn,spikeIn_spec,IgG, wget, ftp)
    samples=pd.read_json(subdic["samples"])
    metadata=pd.read_json(subdic["metadata"])
    inputdf=pd.read_json(subdic["input"])

    lsamples=len(samples)
    lsamples_=len(samples[["Group","Replicate"]].drop_duplicates())
    if lsamples != lsamples_ :
        header="Attention"
        msg='''You have duplicate entries (ie. Group - Replicate combinations). Please correct your input.'''
        return header, msg, dash.no_update

    validation=validate_metadata(metadata)
    if validation:
        header="Attention"
        return header, validation, dash.no_update

    if os.path.isfile(subdic["filename"]):
        header="Attention"
        msg='''You have already submitted this data. Re-submission will not take place.'''
        return header, msg, dash.no_update
    else:
        header="Success!"
        msg='''Please check your email for confirmation.'''
    

    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]
    mps_domain="mpg.de"
    # if user_domain[-len(mps_domain):] == mps_domain :
    # if user_domain !="age.mpg.de" :
    subdic["filename"]=subdic["filename"].replace("/submissions/", "/submissions_ftp/")

    # if user_domain == "age.mpg.de" :
    #     send_submission_email(user=current_user, submission_type="ChIPseq", submission_tag=subdic["filename"], submission_file=None, attachment_path=None)
    # else:
    ftp_user=send_submission_ftp_email(user=current_user, submission_type="CutNTag", submission_tag=subdic["filename"], submission_file=None, attachment_path=subdic["filename"], ftp_user=ftp)
    metadata=pd.concat([metadata,ftp_user])

    EXCout=pd.ExcelWriter(subdic["filename"])
    samples.to_excel(EXCout,"samples",index=None)
    metadata.to_excel(EXCout,"CutNTag",index=None)
    inputdf.to_excel(EXCout,"input",index=None)
    EXCout.save()

    return header, msg, dcc.send_file( subdic["filename"] )

# add rows buttom 
@dashapp.callback(
    Output('samples-table', 'data'),
    Input('editing-rows-button', 'n_clicks'),
    State('samples-table', 'data'),
    State('samples-table', 'columns'))
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

@dashapp.callback(
    Output('input-table', 'data'),
    Input('input-rows-button', 'n_clicks'),
    State('input-table', 'data'),
    State('input-table', 'columns'))
def add_input_row(n_clicks, rows, columns):
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

# navbar toggle for colapsed status
@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open