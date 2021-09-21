import re
from flaski import app
from flask_login import current_user
from flask_caching import Cache
from flaski.routines import check_session_app
from flaski.email import send_submission_email
import dash_table
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, parse_table, protect_dashviews, validate_user_access, \
    make_navbar, make_footer, make_options, make_table, META_TAGS, make_min_width, \
    change_table_minWidth, change_fig_minWidth, GROUPS, make_submission_file, validate_metadata
import uuid
from werkzeug.utils import secure_filename
import json
from flask import session

import pandas as pd
import os

CURRENTAPP="rnaseq"
navbar_title="RNAseq submission form"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title="FLASKI", assets_folder="/flaski/flaski/static/dash/")
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})

input_df=pd.DataFrame( columns=["Sample","Group","Replicate","Read 1", "Read 2"] )
example_input=pd.DataFrame( { "Sample":["mock treated 1","mock treated 2","mock treated 3",
                                        "CDKN1A KD 1","CDKN1A KD 2","CDKN1A KD 3" ] ,
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

style_cell={
        'height': '100%',
        # all three widths are needed
        'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
        'whiteSpace': 'normal'
    }

def generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc):
    # @cache.memoize(60*60*2) # 2 hours
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
        filename=make_submission_file(".RNAseq.xlsx")

        return {"filename": filename, "samples":df, "metadata":df_}
    return _generate_submission_file(rows, email,group,folder,md5sums,project_title,organism,ercc)

input_df=make_table(input_df,'adding-rows-table')
input_df.editable=True
input_df.row_deletable=True
input_df.style_cell=style_cell

example_input=make_table(example_input,'example-table')
example_input.style_cell=style_cell

groups_=make_options(GROUPS)
organisms=["celegans","mmusculus","hsapiens","dmelanogaster","nfurzeri"]
organisms_=make_options(organisms)
ercc_=make_options(["YES","NO"])

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
                dbc.Col( html.Label('Folder name on store-age'),md=3  ), 
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

readme=dcc.Markdown('''

For submitting samples for RNAseq analysis you will need to copy your raw files into `store-age.age.mpg.de/coworking/group_bit_all/automation`. 

Make sure you create a folder eg. `my_proj_folder` and that all your `fastq.gz` files are inside as well as your md5sums file (attention: only one md5sums file per project).

All files will have to be on your project folder (ie. `my_proj_folder`) do not create further subfolders.

Once all the files have been copied, edit the `Samples` and `Info` tabs here and then press submit.

Please check your email for confirmation of your submission.
''', style={"width":"90%", "margin":"10px"} )

controls = [
    dcc.Tabs([
        dcc.Tab( [ readme ], label="Readme", id="tab-readme") ,
        dcc.Tab( [ input_df,
            html.Button('Add Sample', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
            ],
            label="Samples", id="tab-samples",
            ),
        dcc.Tab( [ example_input ],label="Samples (example)", id="tab-samples-example") ,
        dcc.Tab( arguments,label="Info", id="tab-info" ) ,
    ])
]

side_bar=[ dbc.Card(controls, body=False),
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
                        children=html.Div(id="side_bar"),
                        style={"margin-top":"0%"}
                    ),                    
                    style={"width": "90%", "min-height": "100%","height": "100%",'overflow': 'scroll'} ),               
                # dbc.Col( dcc.Loading(
                #         id="loading-output-2",
                #         type="default",
                #         children=[ html.Div(id="my-output")],
                #         style={"margin-top":"50%","height": "100%"} ),
                #     md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"min-height": "87vh"}),
    ] ) 
    ] + make_footer()
)

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
    State('opt-ercc', 'value') )
def update_output(session_id, n_clicks, rows, email,group,folder,md5sums,project_title,organism,ercc):
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
    
    EXCout=pd.ExcelWriter(subdic["filename"])
    samples.to_excel(EXCout,"samples",index=None)
    metadata.to_excel(EXCout,"RNAseq",index=None)
    EXCout.save()

    send_submission_email(user=current_user, submission_type="RNAseq", submission_file=os.path.basename(subdic["filename"]), attachment_path=subdic["filename"])

    return dcc.Markdown(msg, style={"margin-top":"10px"} )

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