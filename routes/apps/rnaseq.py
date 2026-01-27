from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_options, GROUPS, GROUPS_INITALS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import json
import base64
import pandas as pd
import zipfile
from io import BytesIO

from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename

import yaml
import re

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("rnaseq",url_base_pathname=f'{PAGE_PREFIX}/rnaseq/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="RNA seq",  assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/") update_title='Load...', 

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
    eventlog = UserLogging(email=current_user.email, action="visit rnaseq")
    db.session.add(eventlog)
    db.session.commit()

    protected_content=html.Div(
        [
            make_navbar_logged("RNAseq",current_user),
            html.Div(id="app-content", style={"height":"100%","overflow":"scroll"}),
            # html.Div(id="app-content", style={"height":"1380px","width":"100%","overflow":"scroll"}),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

# Read in users input and generate submission file.
def generate_submission_file(rows, email,group,md5sums,project_title,organism, release, ercc, link, ftp, tape):
    @cache.memoize(60*60*2) # 2 hours 60*60*2
    def _generate_submission_file(rows, email,group,md5sums,project_title,organism, release, ercc, link, ftp, tape):
        
        ############################
        # samples/groups dataframe #
        ############################

        df=pd.DataFrame()
        for row in rows:
            if row['Read 1'] != "" :
                df_=pd.DataFrame(row,index=[0])
                df=pd.concat([df,df_])
        df.reset_index(inplace=True, drop=True)
        df.columns=["Read 1","Read 2","Group"]

        for c in df.columns:
            df[c]=df[c].apply(lambda x: str(x).replace("\\x01", "").strip().replace(";","_") )
        for c in ["Read 1","Read 2"]:
            df[c]=df[c].apply( lambda x: str(x).replace(" ", "") )
        df["Group"]=df["Group"].apply( lambda x: str(x).replace(" ", "_") )

        files_for_md5sums=df["Read 1"].tolist() + df["Read 2"].tolist()
        files_for_md5sums=",".join( files_for_md5sums ).replace(",,",",").strip(",")

        df_=df.to_json()

        df = df.to_csv(sep=";", index=False, header=False ).rstrip("\n") # .replace("\n") #, r"\n")
        df = df.strip().strip(";")
        df = df.split("\n")

        if (".fastq.gz" not in files_for_md5sums) and (".fq.gz" not in files_for_md5sums) :
            files_for_md5sums="NONE"
            df=[ s.split(";") for s in df]
            df=[ f"{s[0]};{s[2]}" for s in df if s != "" ]

        ######################
        # metadata dataframe #
        ######################

        meatadf=pd.DataFrame({"Field":["email","Group","md5sums","Project title", "Organism", "release", "ERCC",  "link","ftp", "tape"],\
                          "Value":[email,group,md5sums,project_title, organism,  release, ercc, link, ftp, tape]}, index=list(range(10)))
        meatadf_=meatadf.to_json()

        #########
        # erccs #
        #########

        ercc_dic={ "ercc92" : {
            "url_ercc_gtf" : "https://datashare.mpcdf.mpg.de/s/MOxbNrXeBNcg9wt/download" ,
            "url_ercc_fa" : "https://datashare.mpcdf.mpg.de/s/H9PQu3vDRi9saqV/download"
        }
        }

        ###########
        # folders #
        ###########

        if group != "External" :
            if group in GROUPS :
                project_title=GROUPS_INITALS[group]+"_"+secure_filename(project_title)
                project_folder=group+"/"+project_title
            else:
                user_domain=[ s.replace(" ","") for s in email.split(",") if "mpg.de" in s ]
                user_domain=user_domain[0].split("@")[-1]
                # mps_domain="mpg.de"
                tag=user_domain.split(".mpg.de")[0]

                project_title=tag+"_"+secure_filename(project_title)

                project_folder=group+"/"+project_title
        else:
            project_title="bit_ext_"+secure_filename(project_title)
            project_folder="Bioinformatics/"+project_title

        source_folder_=os.path.join("/nexus/posix0/MAGE-flaski/ftp_data/" , ftp)
        project_folder_=os.path.join("/raven/ptmp/flaski/projects/", project_folder) 
        code_folder_=os.path.join("/nexus/posix0/MAGE-flaski/service/projects/code/", project_folder)
        if ercc not in ercc_dic.keys() :
            genomes_folder_="/nexus/posix0/MAGE-flaski/service/genomes/jawm/"
        else:
            genomes_folder_=os.path.join("/raven/ptmp/flaski/projects/", project_folder, "genone") 

        slurm_yaml_file=os.path.basename( make_submission_file(".RNAseq.slurm.yaml") )
        uploads_file=slurm_yaml_file.replace( ".yaml", ".upload" )
        uploads_file_=f"/nexus/posix0/MAGE-flaski/service/projects/code/Bioinformatics/bit_mpcdf_automation/jawm_submissions/{uploads_file}"
        docker_yaml_file=slurm_yaml_file.replace(".slurm.",".docker.")
        excel_file=slurm_yaml_file.replace(".slurm.yaml",".flaski.xlsx")

        ref_padj=os.path.join( project_folder_, "deseq2_output", "padj.hash.tsv" )

        ##############
        # yaml files #
        ##############

        slurm=rf"""# an hpc yaml rnaseq
- scope: automation
  md5sums: "{md5sums}"
  code_folder: "{code_folder_}"
  source_folder: "{source_folder_}"
  project_folder: "{project_folder_}"
  email: "{email}"
  group: "{group}"
  md5sums: "{md5sums}"
  project_title: "{project_title}"
  link: "{link}"
  ftp: "<ftp_account>"
  files_for_md5sums: "{files_for_md5sums}"
  issue_title: "RNAseq pipeline"
  workflow: "jawm_rnaseq@latest-tag"
  report_file: "{uploads_file_}"
  tape: "{tape}"

- includes:
    - ./jawm_rnaseq/yaml/nexus.apptainer.yaml

- scope: hash
  include: 
    - {ref_padj}
  overwrite: true

- scope: global
  environment: "apptainer"
  automated_mount: False
  manager: slurm
  # environment_apptainer: {{ "-B": "/nexus:/nexus" }}
  # manager_slurm: {{ "-p": "cluster,dedicated" }}
  environment_apptainer: {{ "-B": [ "/nexus:/nexus", "/ptmp:/ptmp", "/raven:/raven" ] }}
  manager_slurm: {{ "--ntasks-per-core":"2" , "-p":"general,small" }}
  before_script: "module load apptainer"
  parallel: True
  var:
    skip_prepull: True
    map.source_folder: "{source_folder_}"
    mk.project_folder: "{project_folder_}"
    map.genomes_folder: "{genomes_folder_}"
    organism: "{organism}"
    release: "{release}"
    groups: |"""
        
        for row in df:
            slurm=f"""{slurm}
      {row}"""
            
        slurm=slurm+rf"""
    report_file: "{uploads_file_}"

- scope: process
  name: 
    - download_link
    - read_acc
    - download_gtf
    - download_dna
    - get_erccs
  manager: local

- scope: process
  name: fastqc
  var:
    cpus: 4

- scope: process
  name: 
    - unstranded_mapping
    - mapping
    - geneid
    - biotype
  var:
    cpus: 12
"""

        docker=rf"""# a docker yaml rnaseq
- scope: global
  environment: "docker"
  parallel: false
  var:
    organism: "organism"
    release: "{release}"
    groups: |"""
        for row in df:
            docker=f"""{docker}
      {row}"""

        if ercc in ercc_dic.keys(): 
            ercc_yaml=rf"""
- scope: process
  name: get_genome
  var:
    ercc_label: "{ercc}"
    url_ercc_gtf: "{ercc_dic[ercc]['url_ercc_gtf']}"
    url_ercc_fa: "{ercc_dic[ercc]['url_ercc_fa']}"
"""
            slurm=slurm+ercc_yaml
            docker=docker+ercc_yaml
                            
        return slurm, docker, slurm_yaml_file, docker_yaml_file, excel_file, meatadf_, df_
    
    return _generate_submission_file( rows, email, group, md5sums, project_title, organism, release, ercc, link, ftp, tape)

@dashapp.callback(
    Output('app-content', component_property='children'),
    Input('session-id', 'data')
)
def make_app_content(session_id):
    header_access, msg_access = check_access( 'rnaseq' )
    # header_access, msg_access = None, None # for local debugging 

    input_df=pd.DataFrame( columns=["Read 1", "Read 2","Group"] )
    example_input=pd.DataFrame( 
        { 
            "Read 1": 
                [ 
                    "A006850092_131904_S2_L002_R1_001.fastq.gz,A003450092_131904_S2_L003_R1_001.fastq.gz",
                    "A006850092_131924_S12_L002_R1_001.fastq.gz",
                    "A006850092_131944_S22_L002_R1_001.fastq.gz",
                    "A006850092_131906_S3_L002_R1_001.fastq.gz",
                    "A006850094_131926_S3_L001_R1_001.fastq.gz",
                    "A006850092_131956_S28_L002_R1_001.fastq.gz"
                ],
            "Read 2": 
                [ 
                "A003450092_131904_S2_L002_R2_001.fastq.gz,A003450092_131904_S2_L003_R2_001.fastq.gz",
                "A006850092_131924_S12_L002_R2_001.fastq.gz",
                "A006850092_131944_S22_L002_R2_001.fastq.gz",
                "A006850092_131906_S3_L002_R2_001.fastq.gz",
                "A006850094_131926_S3_L001_R2_001.fastq.gz",
                "A006850092_131956_S28_L002_R2_001.fastq.gz"
            ],
            "Group" : ['control','control','control','shRNA','shRNA','shRNA'] ,
            "Notes":  
                [
                    "eg. 2 files / sample", "","","","",""
                ]
        }
    )

    # generate dropdown options
    organisms=["homo_sapiens", "mus_musculus", "danio_rerio", "drosophila_melanogaster", "caenorhabditis_elegans", "nothobranchius_furzeri"]
    organisms_=make_options(organisms)
    release=["115"]
    release_=make_options(release)
    ercc_=make_options(["ercc92","none"])

    readme_age='''
    '''

    readme_mps='''
**Data transfer** 

Once you've submited your form you will receive instructions on how to upload your data over FTP.

**Archived data**

For analyzing previously archived data you do not need to transfer your files again. For this in the `md5sums` field you will need to 
type in *TAPE*.
    '''

    readme_common=f'''
**SRA**

If you want to analyse **GEO/SRA** data you can do this without downloading the respective files by giving in 
the SRA run number instead of the file name. In the `md5sums` fields you will need to 
type in *SRA*. An example can be found [here](https://youtu.be/KMtk3NCWVnI). 
'''

    local_readme='''
**Local runs**

For analysing these data on your laptop make sure you have docker and jawm installed:

- https://www.docker.com
- https://github.com/mpg-age-bioinformatics/jawm

Once you have used this web interface to generate your parameters yaml file you can use it to analyse your data locally.

If you are analyzing SRA data you can start the analysis direclty with:
```
jawm jawm_rnaseq -p /path/to/file.yaml
```

If you have local fastq.gz files you can start the analysis with:
```
jawm jawm_rnaseq -p /path/to/file.yaml --global.map.source_folder /path/to/your/fastq/files/
```
'''

    readme_age=f'''
{readme_age}

{readme_common}

{local_readme}
    '''

    readme_mps=f'''
{readme_mps}

{readme_common}

{local_readme}
    '''

#     readme_noaccess='''
# **You have no access to this App.** 

# Once you have been given access more information will be displayed on how to transfer your raw data.
#     '''

    readme_noaccess=local_readme


    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]

    mps_domain="mpg.de"
    if user_domain[-len(mps_domain):] == mps_domain :
        if user_domain =="age.mpg.de" :
            readme=dcc.Markdown(readme_mps, style={"width":"90%", "margin":"10px"} )
            groups_=make_options(GROUPS)
            groups_val=None
            hide_style={"margin-top":10}
        else :
            readme=dcc.Markdown(readme_mps, style={"width":"90%", "margin":"10px"} )
            groups_=make_options([user_domain])
            groups_val=user_domain
            hide_style={"margin-top":10}

    elif not header_access :
        readme=dcc.Markdown(readme_mps, style={"width":"90%", "margin":"10px"} )
        groups_=make_options([user_domain])
        groups_val=user_domain
        hide_style={"margin-top":10,"display": 'none'}
    else:
        readme=dcc.Markdown(readme_noaccess, style={"width":"90%", "margin":"10px"} )
        groups_=make_options(["External"])
        groups_val="External"
        hide_style={"margin-top":10,"display": 'none'}

    input_df=make_table(input_df,'adding-rows-table')
    input_df.editable=True
    input_df.row_deletable=True
    input_df.style_cell=style_cell
    input_df.style_table["height"]="62vh"

    example_input=make_table(example_input,'example-table')
    example_input.style_cell=style_cell
    example_input.style_table["height"]="68vh"

    yes_no_options=[ {'label':'yes', 'value':'yes'}, {'label':'no', 'value':'no'} ]

    # arguments 
    arguments=[ 
        dbc.Row( 
            [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
            ], 
            style=hide_style),
        dbc.Row( 
            [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right"  }), 
                dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, value=groups_val, style={ "width":"100%" }),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'), md=3  ), 
            ], 
            style=hide_style ), # ,'display': hide
        dbc.Row( 
            [
                dbc.Col( html.Label('md5sums') ,md=3 , style={"textAlign":"right", }),  # 'display': hide
                dbc.Col( dcc.Input(id='md5sums', placeholder="md5sums.file.txt", value="", type='text', style={ "width":"100%" } ) ,md=3), # 'display': hide
                dbc.Col( html.Label('File with md5sums'),md=3   )  #, style={'display': hide}
            ], 
            style=hide_style), #'display': hide
        dbc.Row( 
            [
                dbc.Col( html.Label('Project title') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='project_title', placeholder="my_super_proj", value="", type='text', style={ "width":"100%" }, maxLength=32) ,md=3 ),
                dbc.Col( html.Label('Give a name to your project'),md=3  ), 
            ], 
            style=hide_style), # ,'display': hide
        dbc.Row( 
            [
                dbc.Col( html.Label('Organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-organism', options=organisms_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={ "margin-top":10 }),
        dbc.Row( 
            [
                dbc.Col( html.Label('Release') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-release', options=release_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
            ], 
            style={ "margin-top":10 }),
        dbc.Row( 
            [
                dbc.Col( html.Label('ERCC') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-ercc', options=ercc_, value="none", style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('ERCC spikeins'),md=3  ), 
            ], 
            style={ "margin-top":10 }),
        dbc.Row( 
            [
                dbc.Col( html.Label('ftp user') ,md=3 , style={"textAlign":"right" } ) , 
                dbc.Col( dcc.Input(id='ftp', placeholder="ftp user name", value="", type='text', style={ "width":"100%" } ) ,md=3 ),
                dbc.Col( html.Label("if data has already been uploaded please provide the user name used for ftp login"), md=3  ), 
            ], 
            style=hide_style ), # , 'display': hide
        dbc.Row( 
            [
                dbc.Col( html.Label('TAPE') ,md=3 , style={"textAlign":"right", }),  # 'display': hide
                dbc.Col( dcc.Dropdown( id='tape', options=yes_no_options, value="no", style={ "width":"100%" }),md=3 ),
                #dbc.Col( dcc.Input(id='tape', placeholder="tape file", value="", type='text', style={ "width":"100%" } ) ,md=3), # 'display': hide
                dbc.Col( html.Label('Has your data been analysed before and maybe already backed up to tape.'),md=3   )  #, style={'display': hide}
            ], 
            style=hide_style), #'display': hide
        dbc.Row( 
            [
                dbc.Col( html.Label('link') ,md=3 , style={ "textAlign":"right" }), 
                dbc.Col( dcc.Input(id='link', placeholder="wget -r --http-user=NGS_BGarcia_SRE01_A006850205 --http-passwd=qlATOWs0 http://bastet2.ccg.uni-koeln.de/downloads/NGS_BGarcia_SRE01_A006850205", value="", type='text', style={ "width":"100%" } ) ,md=3 ),
                dbc.Col( html.Label("`wget` or similar command for direct download (optional)"),md=3 ), 
            ], 
            style=hide_style ), # ,'display': hide
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
                        dcc.Tab( example_input,label="Samples (example)", id="tab-samples-example") ,
                        dcc.Tab( 
                            [ 
                                html.Div(
                                    input_df,
                                    id="updatable-df"
                                ),
                                html.Button('Add Sample', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Samples", id="tab-samples",
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
        dcc.Download( id="download-file" ),
        # dcc.Download( id="download-file-json" )

    ]

    return content


@dashapp.callback( 
    Output("updatable-df", 'children'),
    Output('email', 'value'),
    Output('opt-group', 'value'),
    Output('md5sums', 'value'),
    Output('project_title', 'value'),
    Output('opt-organism', 'value'),
    Output('release', 'value'),
    Output('opt-ercc', 'value'),
    Output('link', 'value'), 
    Output('ftp', 'value'),
    Output('tape', 'value'),
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
    if "RNAseq" not in exc.sheet_names :
        raise dash.exceptions.PreventUpdate
    samples = pd.read_excel(io.BytesIO(decoded), sheet_name="samples")[["Read 1", "Read 2", "Group"]]
    RNAseq = pd.read_excel(io.BytesIO(decoded), sheet_name="RNAseq")

    samples = samples[ samples.columns.tolist()[:6]]

    input_df=make_table(samples,'adding-rows-table')
    input_df.editable=True
    input_df.row_deletable=True
    input_df.style_cell=style_cell
    input_df.style_table["height"]="62vh"

    values_to_return=[]
    fields_to_return=[ "email", "Group", "md5sums", "Project title", "Organism", "Release", "ERCC", "link", "ftp", "tape" ]
    fields_on_file=RNAseq["Field"].tolist()
    for f in fields_to_return:
        if f in  fields_on_file:
            values_to_return.append(  RNAseq[RNAseq["Field"]==f]["Value"].tolist()[0]  )
        else:
            values_to_return.append( dash.no_update )

    return [ input_df ] +  values_to_return + [ filename ]

# main submission call
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    Output("download-file","data"),
    # Output("download-file-json","data"),
    Input('submit-button-state', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('md5sums', 'value'),
    State('project_title', 'value'),
    State('opt-organism', 'value'),
    State('opt-release', 'value'),
    State('opt-ercc', 'value'),
    State('link', 'value'),
    State('ftp', 'value'),
    State('tape', 'value'),
    prevent_initial_call=True )
def update_output(n_clicks, rows, email, group, md5sums, project_title, organism, release, ercc, link, ftp, tape):
    header, msg = check_access( 'rnaseq' )
    if not msg:
        authorized = True
    else:
        authorized= False

    # header, msg = None, None # for local debugging 
    # if msg :
    #     return header, msg, dash.no_update, dash.no_update

    if not link:
        link="NONE"

    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]
    mps_domain="mpg.de"

    if ( user_domain[-len(mps_domain):] != mps_domain ) and ( authorized ) :
        group="Bioinformatics"


    slurm, docker, slurm_yaml_file, docker_yaml_file, excel_file, meatadf_, df_=generate_submission_file(rows, email,group,md5sums,project_title,organism, release, ercc, link, ftp, tape)

    samples=pd.read_json(df_)
    metadata=pd.read_json(meatadf_)

    validation=validate_metadata(metadata)
    if validation:
        header="Attention"
        return header, validation, dash.no_update


    readmeMD=rf"""# README

For analysing these data on your laptop make sure you have docker and jawm installed:

- https://www.docker.com
- https://github.com/mpg-age-bioinformatics/jawm

If you are analyzing SRA data you can start the analysis direclty with:
```
jawm jawm_rnaseq -p {docker_yaml_file}
```

If you have local fastq.gz files you can start the analysis with:
```
jawm jawm_rnaseq -p {docker_yaml_file} --global.map.source_folder /path/to/your/fastq/files/
```
"""  


    if ( user_domain[-len(mps_domain):] == mps_domain ) or ( authorized ) :

        # if user_domain != "age.mpg.de" :
        slurm_yaml_file=os.path.join("/submissions_ftp/",slurm_yaml_file)
        docker_yaml_file=os.path.join("/submissions_ftp/",docker_yaml_file)
        excel_file=os.path.join("/submissions_ftp/",excel_file)

        if os.path.isfile(slurm_yaml_file):
            header="Attention"
            msg='''You have already submitted this data. Re-submission will not take place.'''
            return header, msg, dash.no_update
        else:
            header="Success!"
            msg='''Please allow a summary file of your submission to download and check your email for confirmation.'''


        EXCout=pd.ExcelWriter(excel_file)
        samples.to_excel(EXCout,"samples",index=None)
        metadata.to_excel(EXCout,"RNAseq",index=None)
        EXCout.save()

        ftp_user=send_submission_ftp_email(user=current_user, submission_type="RNAseq", submission_tag=excel_file, submission_file=os.path.basename(excel_file), attachment_path=excel_file, ftp_user=ftp)

        metadata=metadata[ metadata["Field"] != "ftp" ]
        metadata=pd.concat([metadata,ftp_user])

        EXCout=pd.ExcelWriter(excel_file)
        samples.to_excel(EXCout,"samples",index=None)
        metadata.to_excel(EXCout,"RNAseq",index=None)
        EXCout.save()

        ftp_user=ftp_user["Value"].tolist()[0]
        slurm=slurm.replace("<ftp_account>", ftp_user)
    
        with open(slurm_yaml_file, "w") as out:
            out.write(slurm)
        with open(docker_yaml_file, "w") as out:
            out.write(docker)

        def write_archive(bytes_io):
            with zipfile.ZipFile(bytes_io, mode="w") as zf:
                for f in [ slurm_yaml_file, docker_yaml_file, excel_file ]:
                    zf.write(f,  os.path.basename(f) )

        return header, msg, dcc.send_bytes(write_archive, os.path.basename(excel_file).replace("xlsx","zip") )


    else:

        metadata=metadata.astype(str)
        metadata=metadata[~metadata["Value"].isin( [ "", "NONE", "none", "External" ]) ]
        metadata=metadata[~metadata["Field"].isin( [ "email" ]) ]


        def write_archive(bytes_io):
            # 1) build the Excel in memory
            excel_buf = BytesIO()
            with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
                samples.to_excel(writer, sheet_name="samples", index=False)
                metadata.to_excel(writer, sheet_name="RNAseq", index=False)
            excel_bytes = excel_buf.getvalue()

            # 2) write everything into the zip (all in memory)
            with zipfile.ZipFile(bytes_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(os.path.basename(docker_yaml_file), docker)         # YAML string
                zf.writestr(os.path.basename(excel_file), excel_bytes)          # XLSX bytes
                zf.writestr("README.md", readmeMD)                              # README string

        zip_name = os.path.basename(excel_file).replace(".xlsx", ".zip")

        header="Success!"
        msg='''Please allow a zip file with the relevant files of your submission to download.'''

        return header, msg, dcc.send_bytes(write_archive, zip_name)


# add rows buttom 
@dashapp.callback(
    Output('adding-rows-table', 'data'),
    Input('editing-rows-button', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('adding-rows-table', 'columns'))
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

# navbar toggle for colapsed status
@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

