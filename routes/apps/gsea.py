from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
from flask import session
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, parse_table, make_options, GROUPS, make_table, make_submission_file, validate_metadata, send_submission_email, send_submission_ftp_email
import os
import uuid
import io
import base64
import pandas as pd
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from werkzeug.utils import secure_filename

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("gsea",url_base_pathname=f'{PAGE_PREFIX}/gsea/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="GSEA" ,  assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/") update_title='Load...', 

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
    eventlog = UserLogging(email=current_user.email, action="visit gsea")
    db.session.add(eventlog)
    db.session.commit()

    protected_content=html.Div(
        [
            make_navbar_logged("GSEA",current_user),
            html.Div(id="app-content", style={"height":"100%","overflow":"scroll"}),
            # html.Div(id="app-content", style={"height":"1380px","width":"100%","overflow":"scroll"}),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content


# Read in users input and generate submission file.
def generate_submission_file(rows, expression,genessets, email,group,folder,project_title,organism,ref):
    @cache.memoize(60*60*2) # 2 hours
    def _generate_submission_file(rows, expression,genessets, email,group,folder,project_title,organism,ref):
        df=pd.DataFrame()
        for row in rows:
            if row['Sample'] != "" :
                df_=pd.DataFrame(row,index=[0])
                df=pd.concat([df,df_])
        df.reset_index(inplace=True, drop=True)

        edf=pd.DataFrame()
        for row in expression:
            df_=pd.DataFrame(row,index=[0])
            edf=pd.concat([edf,df_])
        edf.reset_index(inplace=True, drop=True)

        gdf=pd.DataFrame()
        for row in genessets:
            df_=pd.DataFrame(row,index=[0])
            gdf=pd.concat([gdf,df_])
        gdf.reset_index(inplace=True, drop=True)

        reference_len=len(df[df["Group"]==ref])
        target=df[df["Group"]!=ref]["Group"].tolist()[0]
        target_len=len(df[df["Group"]==target])
        
        df_=pd.DataFrame({"Field":["email","Group","Folder","Project title", "Organism",\
                          "Reference", "Reference_len", "Target", "Target_len"],\
                          "Value":[email,group,folder,project_title, organism,ref,\
                              reference_len, target,target_len ]}, index=list(range(9)))
        df=df.to_json()
        edf=edf.to_json()
        gdf=gdf.to_json()
        df_=df_.to_json()
        filename=make_submission_file(".GSEA.xlsx", folder="mpcdf")

        return {"filename": filename, "samples":df, "expression":edf ,"metadata":df_, "gene_sets":gdf}
    return _generate_submission_file(rows,expression, genessets, email,group,folder,project_title,organism,ref)

@dashapp.callback(
    Output('app-content', component_property='children'),
    Input('session-id', 'data')
)
def make_app_content(session_id):
    header_access, msg_access = check_access( 'gsea' )

    # base samples input dataframe and example dataframe
    input_df=pd.DataFrame( columns=["Sample","Group","Replicate",] )
    example_input=pd.DataFrame( { 
        "Sample":["A","B","C", "D","E","F" ] ,
        "Group" : ['control','control','control','shRNA','shRNA','shRNA'] ,
        "Replicate": ['1','2','3','1','2','3'] } )
    exp_matrix="NAME	DESCRIPTION	A	B	C	D	E	F\n\
NFKBIA	ENSG00000100906	1590.539243	1527.33925	1573.351161	16183.3712	16320.43434	15237.23716\n\
PPP1R15A	ENSG00000087074	1218.545441	1121.411948	1163.753201	10086.79432	10447.23679	9197.93721\n\
RNF169	ENSG00000166439	2252.321089	2332.640984	2199.113968	9131.24871	9296.763661	9077.958905\n\
GEM	ENSG00000164949	660.4887926	679.1717358	586.0728326	4355.135205	4316.806886	4390.000304\n\
PPP1R18	ENSG00000146112	3527.924828	3642.170091	3387.474886	13858.63893	14048.57205	14201.88159\n\
DNAJA1	ENSG00000086061	13751.59167	12997.91859	12846.73404	2120.955793	2056.616042	1977.421084\n\
IER3	ENSG00000137331	1351.487645	1348.035176	1297.059738	36065.1493	35578.59032	32753.08877\n\
CHMP1B	ENSG00000255112	3368.154744	3282.467361	3591.49163	14511.69882	14016.15949	14772.62859\n\
FEM1B	ENSG00000169018	3418.219733	3157.526486	3214.296535	12211.31235	11803.47844	11846.67276\n\
WEE1	ENSG00000166483	4392.344451	4696.521162	4754.110541	16424.21638	16204.16747	16530.27408\n\
KRT17	ENSG00000128422	27672.31547	27760.10429	26734.26201	226456.5886	225772.6386	221115.2843\n\
AMOTL2	ENSG00000114019	2798.197954	2803.625444	2722.671164	16516.39898	16400.54031	16478.57564\n\
TPPP	ENSG00000171368	770.5020684	744.5534366	758.549637	6001.99581	6300.908614	5826.095545\n\
MCL1	ENSG00000143384	11970.71259	11874.58744	11421.54805	75053.4836	73025.38499	74519.55414\n\
PIM1	ENSG00000137193	1571.503178	1582.816	1626.059079	9585.93767	9045.513628	9585.269416\n\
NR4A2	ENSG00000153234	1314.740387	1314.442891	1339.011899	10886.99942	10945.84909	10384.33159\n\
RND3	ENSG00000115963	3916.985794	3846.362467	3718.609533	30830.15766	30229.36613	30600.05908\n\
BCL3	ENSG00000069399	1485.359618	1366.312543	1220.46115	10413.51195	10959.09114	9437.325147\n\
TUFT1	ENSG00000143367	1433.614772	1385.34518	1353.508779	7656.83506	8020.348168	7556.787112\n\
MT-ND1	ENSG00000198888	197170.7675	181605.9784	171256.6388	28109.39048	24834.26612	25967.72544\n\
ARHGEF4	ENSG00000136002	2812.642639	2904.621831	2712.837982	10924.56589	11142.58926	10998.66134\n\
MEGF8	ENSG00000105429	5603.643213	5720.168547	5518.485642	977.6582766	910.5157063	938.346575\n\
PTP4A1	ENSG00000112245	31052.57057	30262.78247	28888.7064	105140.6298	102471.0358	108995.5142\n\
DSEL	ENSG00000171451	9231.379027	9457.966961	9179.964965	1814.973434	1843.909721	1780.057859\n\
GJC1	ENSG00000182963	1703.664291	1767.870699	1737.140594	8052.004508	7640.118309	7436.09964\n\
ELL2	ENSG00000118985	3746.774768	3996.832408	3921.038174	20467.96073	21250.83455	21601.92426\n\
CKAP2L	ENSG00000169607	1729.282951	1773.032574	1568.830263	9485.571529	9267.734555	10225.98838\n\
THBS1	ENSG00000137801	13499.2319	14166.79245	13644.89031	67848.96656	67703.88733	69798.34048\n\
TGIF1	ENSG00000177426	2216.361094	2222.499967	2113.919935	9239.194851	9308.238286	9728.431128\n\
RSAD1	ENSG00000136444	1963.987311	1968.67234	2012.470031	7157.091796	7425.047039	7190.780561\n\
IRAK2	ENSG00000134070	532.6009934	473.7024705	534.6411499	4096.331572	4056.905207	4293.856087\n\
CREM	ENSG00000095794	1745.004028	1825.174824	1728.412992	6918.870004	6964.196391	6842.573694\n\
PHLDB2	ENSG00000144824	3415.137582	3633.518663	3591.099451	13783.13208	14218.5484	14514.8009\n\
CYR61	ENSG00000142871	8210.957428	8671.115705	7973.737967	363492.8723	348255.5201	322380.1049"

    genes_sets="GeneSet	GeneSet_description	Genes\n\
REACTOME_ION_CHANNEL_TRANSPORT 	http://www.gsea-msigdb.org/gsea/msigdb/cards/REACTOME_ION_CHANNEL_TRANSPORT	CLCN6	CLCA1	CLCA4	ATP2C1	ATP1A2	ATP6V0A1	BEST2	ATP6V1H	ANO2	NEDD4L	ATP9A	MCOLN3	ATP11B	CAMK2B	ATP2B4	WNK1	ATP2C2	ATP2B3	ATP11A\n\
REACTOME_SIGNALING_BY_THE_B_CELL_RECEPTOR_BCR	http://www.gsea-msigdb.org/gsea/msigdb/cards/REACTOME_SIGNALING_BY_THE_B_CELL_RECEPTOR_BCR 	CD79B	PSMB1	BTK	FYN	CD22	PSMC4	PSMA4	CUL1	PSME4	DAPP1	NFATC3	FBXW11	PSMC5	FKBP1A	PSME1	PSMD5	BLNK	ITPR3	PSMD8	PSMC6	PSMA3"

    # improve tables styling
    style_cell={
            'height': '100%',
            # all three widths are needed
            'minWidth': '130px', 'width': '130px', 'maxWidth': '180px',
            'whiteSpace': 'normal'
        }

    #style_table={"height": "75vh", "maxHeight": "75vh",'width':"100%",'overflowY': 'auto', 'overflowX': 'auto','border': '1px solid rgb(223,223,223)'},

    def reshape_tables(table):
        table.style_table["height"]="68vh"
        # table.style_table["min-height"]="68vh"
        return table

    input_df=make_table(input_df,'adding-rows-table')
    input_df.editable=True
    input_df.row_deletable=True
    input_df.style_cell=style_cell
    input_df=reshape_tables(input_df)


    example_input=make_table(example_input,'example-table')
    example_input.style_cell=style_cell
    example_input=reshape_tables(example_input)


    exp_matrix=exp_matrix.split("\n")
    exp_matrix=[ s.split("\t") for s in exp_matrix ]
    exp_matrix=pd.DataFrame(exp_matrix[1:], columns=exp_matrix[0])
    exp_matrix=make_table(exp_matrix,'expression-table')
    exp_matrix.style_cell=style_cell
    exp_matrix=reshape_tables(exp_matrix)


    genes_sets=genes_sets.split("\n")
    genes_sets=[ s.split("\t") for s in genes_sets ]
    genes_sets_cols=genes_sets[0]
    genes_sets=genes_sets[1:]
    cols_size=max([ len(s) for s in genes_sets ])
    i=len(genes_sets_cols)
    while len(genes_sets_cols) < cols_size:
        genes_sets_cols=genes_sets_cols+["Unnamed: %s" %str(i)]
        i=i+1
    genes_sets=pd.DataFrame(genes_sets, columns=genes_sets_cols)
    genes_sets=make_table(genes_sets,'genes_sets-table')
    genes_sets.style_cell=style_cell
    genes_sets=reshape_tables(genes_sets)


    # generate dropdown options
    groups_=make_options(GROUPS)
    external_=make_options(["External"])
    organisms=["celegans","mmusculus","hsapiens","dmelanogaster","nfurzeri"]
    organisms_=make_options(organisms)
    ercc_=make_options(["YES","NO"])

    user_domain=current_user.email
    user_domain=user_domain.split("@")[-1]

    #if user_domain[-len(mps_domain):] == mps_domain :
    if user_domain =="age.mpg.de" :
        groups_=make_options(GROUPS)
        groups_val=None
    else:
        groups_=make_options(["External"])
        groups_val="External"

    folder="GSEA"

    # arguments 
    arguments=[ dbc.Row( [
                dbc.Col( html.Label('email') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='email', placeholder="your.email@age.mpg.de", value=current_user.email, type='text', style={ "width":"100%","height":"35px"} ) ,md=3 ),
                dbc.Col( html.Label('your email address'),md=3  ), 
                ], style={"margin-top":10, "margin-bottom":5}),
            dbc.Row( [
                dbc.Col( html.Label('Group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-group', options=groups_, value=groups_val, style={ "width":"100%","height":"35px"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":5, "margin-bottom":5}),
            dbc.Row( [
                dbc.Col( html.Label('Folder') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='folder', placeholder="my_proj_folder", value=folder, type='text', style={ "width":"100%" } ) ,md=3 ),
                dbc.Col( html.Label('Folder containing your files'),md=3  ), 
            ], style={"margin-top":10, 'display': 'none' }),
            dbc.Row( [
                dbc.Col( html.Label('Project title') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='project_title', placeholder="my_super_proj", value="", type='text', style={ "width":"100%","height":"35px"}, maxLength=32) ,md=3 ),
                dbc.Col( html.Label('Give a name to your project'),md=3  ), 
                ], style={"margin-top":5, "margin-bottom":5}),
            dbc.Row( [
                dbc.Col( html.Label('Organism') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Dropdown( id='opt-organism', options=organisms_, style={ "width":"100%","height":"35px"}),md=3 ),
                dbc.Col( html.Label('Select from dropdown menu'),md=3  ), 
                ], style={"margin-top":5, "margin-bottom":5}),
            dbc.Row( [
                dbc.Col( html.Label('Reference group') ,md=3 , style={"textAlign":"right" }), 
                dbc.Col( dcc.Input(id='reference_group', placeholder="control", value="", type='text', style={ "width":"100%","height":"35px"} ) ,md=3 ),
                dbc.Col( html.Label('Reference group in your sample set'),md=3  ), 
                ], style={"margin-top":5, "margin-bottom":10}),
]

    expression_upload=dcc.Upload(
        id='upload-expression',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')], style={ 'textAlign': 'center', "margin-top": 3, "margin-bottom": 3} 
        ),
        style={
            'width': '98%',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            "margin-top": 10, "margin-bottom": 10,
            "margin-left": "auto", "margin-right": "auto", 
            'textAlign': 'center'
        },
        # Allow multiple files to be uploaded
        multiple=False
    )

    genesets_upload=dcc.Upload(
        id='upload-genesset',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')], style={ 'textAlign': 'center', "margin-top": 3, "margin-bottom": 3} 
        ),
        style={
            'width': '98%',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            "margin-top": 10, "margin-bottom": 10,
            "margin-left": "auto", "margin-right": "auto", 
            'textAlign': 'center'
        },
        # Allow multiple files to be uploaded
        multiple=False
    )

    main_input=[ 
        dbc.Card(
            [
                dcc.Tabs(
                    [
                        # dcc.Tab( label="Readme", id="tab-readme") ,
                        dcc.Tab( [ input_df,
                            html.Button('Add Sample', id='editing-rows-button', n_clicks=0, style={"margin-top":4, "margin-bottom":4})
                            ],
                            label="Samples", id="tab-samples",
                            ),
                        dcc.Tab( [ example_input ],label="Samples (example)", id="tab-samples-example") ,
                        dcc.Tab( [ expression_upload, exp_matrix ], label="Expression", id="tab-expression") ,
                        dcc.Tab( [ genesets_upload, genes_sets ], label="Gene sets", id="tab-genessets") ,
                        dcc.Tab( arguments, label="Info", id="tab-info" ) ,
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

    return main_input


@dashapp.callback(
    Output('expression-table', 'data'),
    Output('expression-table', 'columns'),
    Input('session-id', 'data'),
    Input('upload-expression', 'contents'),
    State('upload-expression', 'filename'),
    State('upload-expression', 'last_modified'),
    prevent_initial_call=True )
def upload_expression(session_id, contents,filename, last_modified):
    df=parse_table(contents,filename,last_modified,session_id,cache, "gsea")
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]

@dashapp.callback(
    Output('genes_sets-table', 'data'),
    Output('genes_sets-table', 'columns'),
    Input('session-id', 'data'),
    Input('upload-genesset', 'contents'),
    State('upload-genesset', 'filename'),
    State('upload-genesset', 'last_modified'),
    prevent_initial_call=True )
def upload_genesets(session_id, contents,filename, last_modified):
    df=parse_table(contents,filename,last_modified,session_id,cache, "gsea")
    return df.to_dict('records'), [{"name": i, "id": i} for i in df.columns]
    
@dashapp.callback(
    Output("modal_header", "children"),
    Output("modal_body", "children"),
    Output("download-file","data"),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('adding-rows-table', 'data'),
    State('expression-table', 'data'),
    State('genes_sets-table', 'data'),
    State('email', 'value'),
    State('opt-group', 'value'),
    State('folder', 'value'),
    State('project_title', 'value'),
    State('opt-organism', 'value'),
    State('reference_group', 'value'),
    prevent_initial_call=True )
def update_output(session_id, n_clicks, rows, expression, genessets, email,group,folder, project_title,organism,ref):
    # apps=read_private_apps(current_user.email,app)
    # apps=[ s["link"] for s in apps ]
    # if not validate_user_access(current_user,CURRENTAPP):
    #         return dcc.Location(pathname="/index", id="index"), None, None
    # if CURRENTAPP not in apps:
    #     return dbc.Alert('''You do not have access to this App.''',color="danger")
    header, msg = check_access( 'gsea' )
    # header, msg = None, None # for local debugging 
    if msg :
        return header, msg, dash.no_update

    subdic=generate_submission_file(rows, expression, genessets,  email,group,folder, project_title,organism,ref)
    samples=pd.read_json(subdic["samples"])
    metadata=pd.read_json(subdic["metadata"])
    expression=pd.read_json(subdic["expression"])
    gene_sets=pd.read_json(subdic["gene_sets"])

    # print(subdic["filename"])

    #{"filename": filename, "samples":df, "metadata":df_}
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
        msg='''Please allow a summary file of your submission to download and check your email for confirmation.'''
    
    # if metadata[  metadata["Field"] == "Group"][ "Value" ].values[0] == "External" :
    #     subdic["filename"]=subdic["filename"].replace("/submissions/", "/tmp/")

    # {"filename": filename, "samples":df, "expression":edf ,"metadata":df_, "gene_sets":gdf}
    EXCout=pd.ExcelWriter(subdic["filename"])
    samples.to_excel(EXCout,"samples",index=None)
    metadata.to_excel(EXCout,"GSEA",index=None)
    expression.to_excel(EXCout,"ExpMatrix",index=None)
    gene_sets.to_excel(EXCout,"GeneSets",index=None)
    EXCout.save()

    send_submission_email(user=current_user, submission_type="GSEA", submission_tag=subdic["filename"], submission_file=None, attachment_path=None)

    # if user_domain == "age.mpg.de" :
    #     send_submission_email(user=current_user, submission_type="GSEA", submission_tag=subdic["filename"], submission_file=None, attachment_path=None)
    # else:
    # ftp_user=send_submission_ftp_email(user=current_user, submission_type="GSEA", submission_tag=subdic["filename"], submission_file=None, attachment_path=subdic["filename"])
    # metadata=pd.concat([metadata,ftp_user])

    # EXCout=pd.ExcelWriter(subdic["filename"])
    # samples.to_excel(EXCout,"samples",index=None)
    # metadata.to_excel(EXCout,"GSEA",index=None)
    # expression.to_excel(EXCout,"ExpMatrix",index=None)
    # gene_sets.to_excel(EXCout,"GeneSets",index=None)
    # EXCout.save()

    return header, msg, dcc.send_file( subdic["filename"] )

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

@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")]
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


