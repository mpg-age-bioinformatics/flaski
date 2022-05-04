from flaski import app
from flask_login import current_user
from flask_caching import Cache
from flaski.email import send_submission_email
from flaski.routines import read_private_apps, separate_apps
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, protect_dashviews, validate_user_access, \
    make_navbar, make_footer, make_options, make_table, META_TAGS, GROUPS, make_submission_file, validate_metadata
import uuid
import pandas as pd
import os

CURRENTAPP="asplicing"
navbar_title="Alternative splicing submission form"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

if app.config["CACHE_TYPE"] == "RedisCache" :
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

# Read in users input and generate submission file.
def generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc):
        df=pd.DataFrame()
        for row in rows:
            if row['Read 1'] != "" :
                df_=pd.DataFrame(row,index=[0])
                df=pd.concat([df,df_])
        df.reset_index(inplace=True, drop=True)
        df_=pd.DataFrame({"Field":["email","Group","Folder","md5sums","Project title", "Organism", "ERCC"],\
                          "Value":[email,group,folder,md5sums,project_title, organism, ercc]}, index=list(range(7)))
        df=df.to_json()
        df_=df_.to_json()
        filename=make_submission_file(".alternativeSplicing.xlsx")

        return {"filename": filename, "samples":df, "metadata":df_}
    return _generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc)


# base samples input dataframe and example dataframe
input_df=pd.DataFrame( columns=["Sample","Group","Replicate","Read 1", "Read 2"] )
example_input=pd.DataFrame( { "Sample":["A","B","C",
                                        "D","E","F" ] ,
                             "Group" : ['control','control','control','shRNA','shRNA','shRNA'] ,
                             "Replicate": ['1','2','3','1','2','3'],
                             "Read 1": [ "A006850092_131904_S2_L002_R1_001.fastq.gz,A003450092_131904_S2_L003_R1_001.fastq.gz",
                                        "A006850092_131924_S12_L002_R1_001.fastq.gz",
                                        "A006850092_131944_S22_L002_R1_001.fastq.gz",
                                        "A006850092_131906_S3_L002_R1_001.fastq.gz",
                                        "A006850094_131926_S3_L001_R1_001.fastq.gz",
                                        "A006850092_131956_S28_L002_R1_001.fastq.gz"],
                                        "Read 2": [ "A003450092_131904_S2_L002_R2_001.fastq.gz,A003450092_131904_S2_L003_R2_001.fastq.gz",
                                        "A006850092_131924_S12_L002_R2_001.fastq.gz",
                                        "A006850092_131944_S22_L002_R2_001.fastq.gz",
                                        "A006850092_131906_S3_L002_R2_001.fastq.gz",
                                        "A006850094_131926_S3_L001_R2_001.fastq.gz",
                                        "A006850092_131956_S28_L002_R2_001.fastq.gz"],
                            "Notes":  ["eg. 2 files / sample", "","","","","",]
                            } )

# improve tables styling
style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

input_df=make_table(input_df,'adding-rows-table')
input_df.editable=True
input_df.row_deletable=True
input_df.style_cell=style_cell

example_input=make_table(example_input,'example-table')
example_input.style_cell=style_cell

# generate dropdown options
groups_=make_options(GROUPS)
external_=make_options(["External"])
organisms=["celegans","mmusculus","hsapiens","dmelanogaster","nfurzeri"]
organisms_=make_options(organisms)
ercc_=make_options(["YES","NO"])

# arguments 
arguments=[ dbc.Row( [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Folder') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='folder', placeholder="my_proj_folder", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Folder containing your files'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('md5sums') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='md5sums', placeholder="md5sums.file.txt", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('File with md5sums'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Project title') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='project_title', placeholder="my_super_proj", value="", type='text', style={ "width":"100%"} ) ,md=3 ),
                dbc.Col( html.Label('Give a name to your project'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('Organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-organism', options=organisms_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":10}),
            dbc.Row( [
                dbc.Col( html.Label('ERCC') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-ercc', options=ercc_, style={ "width":"100%"}),md=3 ),
                dbc.Col( html.Label('ERCC spikeins'),md=3  ), 
                ], style={"margin-top":10,"margin-bottom":10}),        
]

# input 
controls = [
    dcc.Tabs([
        dcc.Tab( label="Readme", id="tab-readme") ,
        dcc.Tab( [ input_df,
            html.Button('Add Sample', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
            ],
            label="Samples", id="tab-samples",
            ),
        dcc.Tab( [ example_input ],label="Samples (example)", id="tab-samples-example") ,
        dcc.Tab( arguments,label="Info", id="tab-info" ) ,
    ])
]

main_input=[ dbc.Card(controls, body=False),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "200px","margin-top":4, "margin-bottom":4}),
            html.Div(id="message")
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
                        children=html.Div(id="main_input"),
                        style={"margin-top":"0%"}
                    ),                    
                    style={"width": "90%", "min-height": "100%","height": "100%",'overflow': 'scroll'} )
            ], 
             style={"min-height": "87vh"}),
    ] ) 
    ] + make_footer()
)

# main submission call
@dashapp.callback(
    Output('message', component_property='children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('folder', 'value'),
    State('md5sums', 'value'),
    State('project_title', 'value'),
    State('opt-organism', 'value'),
    State('opt-ercc', 'value'),
    prevent_initial_call=True )
def update_output(session_id, n_clicks, rows, email,group,folder,md5sums,project_title,organism,ercc):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ] 
    if CURRENTAPP not in apps:
        return dbc.Alert('''You do not have access to this App.''',color="danger")

    # if not validate_user_access(current_user,CURRENTAPP):
    #         return dcc.Location(pathname="/index", id="index"), None, None
    subdic=generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc)
    samples=pd.read_json(subdic["samples"])
    metadata=pd.read_json(subdic["metadata"])
    #{"filename": filename, "samples":df, "metadata":df_}

    validation=validate_metadata(metadata)
    if validation:
        msg='''
#### !! ATTENTION !!

'''+validation
        return dcc.Markdown(msg, style={"margin-top":"15px"} )

    if os.path.isfile(subdic["filename"]):
        msg='''You have already submitted this data. Re-submission will not take place.'''
    else:
        msg='''**Submission successful**. Please check your email for confirmation.'''
    
    if metadata[  metadata["Field"] == "Group"][ "Value" ].values[0] == "External" :
        subdic["filename"]=subdic["filename"].replace("/submissions/", "/tmp/")

    EXCout=pd.ExcelWriter(subdic["filename"])
    samples.to_excel(EXCout,"samples",index=None)
    metadata.to_excel(EXCout,'alternativeSplicing',index=None)
    EXCout.save()

    send_submission_email(user=current_user, submission_type="alternativeSplicing", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])

    if metadata[  metadata["Field"] == "Group"][ "Value" ].values[0] == "External" :
        os.remove(subdic["filename"])

    return dcc.Markdown(msg, style={"margin-top":"10px"} )

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

# this call back prevents the side bar from being shortly 
# shown / exposed to users without access to this App
@dashapp.callback( Output('app_access', 'children'),
                   Output('main_input', 'children'),
                   Output('navbar','children'),
                   Input('session-id', 'data') )
def get_side_bar(session_id):
    if not validate_user_access(current_user,CURRENTAPP):
        return dcc.Location(pathname="/index", id="index"), None, None, None
    else:
        navbar=make_navbar(navbar_title, current_user, cache)
        return None, main_input, navbar


# options and values based on in-house vs external users
@dashapp.callback( Output("tab-readme",'children'),
                   Output("opt-group","options"),
                   Output("opt-group","value"),
                   Input('session-id', 'data') )
def make_readme(session_id):
    apps=read_private_apps(current_user.email,app)
    apps=[ s["link"] for s in apps ] 

    readme_common='''

Make sure you create a folder eg. `my_proj_folder` and that all your `fastq.gz` files are inside as well as your md5sums file (attention: only one md5sums file per project).

All files will have to be on your project folder (eg. `my_proj_folder` in `Info` > `Folder`) do not create further subfolders.

Once all the files have been copied, edit the `Samples` and `Info` tabs here and then press submit.

Samples will be renamed to `Group_Replicate.fastq.gz`! Group -- Replicate combinations should be unique or files will be overwritten.
        '''
    
    sra_samples='''
If you want to analyse **GEO/SRA** data you can do this without downloading the respective files by giving in 
the SRA run number instead of the file name. If you are analysing paired end data and only one run number 
exists please give in the same run number in `Read 2`. In the `Folder` and `md5sums` fields you will need to 
give in *SRA*. An example can be found [here](https://youtu.be/KMtk3NCWVnI). 
    '''

    if CURRENTAPP not in apps:
        readme='''**You have no access to this App.** Once you have been given access more information will be displayed on how to transfer your raw data.
        
        %s

Please check your email for confirmation of your submission.
        ''' %(readme_common)
    else:
        if "@age.mpg.de" in current_user.email:

            readme='''For submitting samples for analysis you will need to copy your raw files into `smb://octopus/group_bit_automation`.
            
            %s

            %s

Please check your email for confirmation of your submission.

            ''' %(readme_common,sra_samples)
        else:
            readme='''In `Info` > `Folder` please type *TAPE*.

Please check your email for confirmation of your submission.
        '''

    readme=dcc.Markdown(readme, style={"width":"90%", "margin":"10px"} )
    
    if "@age.mpg.de" in current_user.email:
        return readme, groups_, None
    else:
        return readme, external_, "External"



# update user email on email field on start
@dashapp.callback( Output('email','value'),
                   Input('session-id', 'data') )
def set_email(session_id):
    return current_user.email

# navbar toggle for colapsed status
@dashapp.callback(
        Output("navbar-collapse", "is_open"),
        [Input("navbar-toggler", "n_clicks")],
        [State("navbar-collapse", "is_open")])
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open