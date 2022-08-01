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
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session, encode_session_file
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

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("storage",url_base_pathname=f'{PAGE_PREFIX}/storage/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

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
        dcc.Location( id='url', refresh=False ),
        html.Div( id="protected-content" ),
    ] 
)

card_label_style={"margin-top":"5px"}
card_input_style={"width":"100%","height":"35px"}
card_body_style={ "padding":"2px", "padding-top":"4px"}
# card_body_style={ "padding":"2px", "padding-top":"4px","padding-left":"18px"}

def time_humanize(timestamp):
    mdate = datetime.utcfromtimestamp(timestamp)
    return humanize.naturaltime(mdate)

def get_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            # folders wich are symb links do not get walked through with os.walk
            #  no risk for admin links to ice cream support
            # also, users are not able to generate . (dot) folders due to secure_filename
            if ( not os.path.islink(fp) ) & ( ".sessions" not in str(fp)  ) :
                total_size += os.path.getsize(fp)
    return total_size

def get_type(mode):
    if stat.S_ISDIR(mode) or stat.S_ISLNK(mode):
        type = 'dir'
    else:
        type = 'file'
    return type

def make_finder(contents, contents_df, sortby, user_path):

    if sortby:
        sb=list(sortby.keys())[0]
        if sortby[ sb ] == "ascending" :
            asc=True
        else:
            asc=False
        contents_df=contents_df.sort_values(by=[ sb ], ascending=asc)
    else:
        contents_df=contents_df.sort_values(by=[ "mod" ], ascending=False)

    files=os.listdir(user_path)

    icons={"Delete":"fas fa-trash-alt","Load":"fas fa-spinner", "Download": "fas fa-file-download"}
    def make_icon(field, filename,ft=['dir','file'],contents=contents, icons=icons):
        info=contents[filename]
        if info["type"] in ft:
            field_=info[field]
            ic=dcc.Link(
                [
                    html.I(className=icons[field])
                ],
                href=f'{PAGE_PREFIX}/storage/{field_}',
                refresh=True
            )
        else:
            ic=""
        return ic


    def make_dir_links(filename,contents=contents):
        info=contents[filename]
        if info["type"] == "dir":
            ui_path_=info['ui_path']
            dl=dcc.Link(
                [
                    filename
                ],
                href=f'{PAGE_PREFIX}{ui_path_}', 
                refresh=False
            )
        else:
            dl=filename
        return dl


    contents_df=contents_df[["Delete", "Name",  "Size",'Modified', "Load", "Download"]]
    contents_df["Delete"]=contents_df["Name"].apply(lambda x:  make_icon( "Delete" , x )  )
    contents_df["Load"]=contents_df["Name"].apply(lambda x:  make_icon( "Load" ,x,  ft=['file'])  )
    contents_df["Download"]=contents_df["Name"].apply(lambda x:  make_icon( "Download" ,x , ft=['file'])  )
    contents_df["Name"]=contents_df["Name"].apply(lambda x:  make_dir_links( x )  )


    contents_df.columns=[ dbc.Button("Delete", id='finder-delete', disabled=True, color="black", style={"text-align":"left"}),\
        dbc.Button("Name", id="finder-name", color="black", style={"textAlign":"left"}),\
        dbc.Button("Size", id="finder-size", color="black", style={"textAlign":"left"}),\
        dbc.Button("Modified", id="finder-modified", color="black", style={"textAlign":"left"}),\
        dbc.Button("Load", id="finder-load", disabled=True, color="black", style={"textAlign":"left"}),\
        dbc.Button("Download", id="finder-download", disabled=True, color="black", style={"textAlign":"left"}) ]

    contents_df=dbc.Table.from_dataframe(contents_df, striped=True, bordered=False, hover=True)

    finder=dbc.Card(
        dbc.Form(
            [ 
                contents_df
            ]
        ),
        body=False,
        # style={"overflow":"scroll"}
    )

    return finder

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('session-id', 'data'),
    State('url', 'pathname')) 
def make_layout(sessionid, ui_path):
    bar=make_navbar_logged("Storage",current_user)
    if len(ui_path) > len(f"{PAGE_PREFIX}/storage/load/"):
        if ui_path[:len(f"{PAGE_PREFIX}/storage/load/")] == f"{PAGE_PREFIX}/storage/load/" :
            bar=None
    
    protected_content=html.Div(
        [
            html.Div(id="mkdir-refresh"),
            dcc.Download( id="download-session" ),
            dcc.Store( data=None, id='sortby' ),
            dcc.Store( data=None, id='saveas' ),
            bar,
            dcc.Loading(
                id="loading-output",
                type="default",
                children=[
                    html.Div(id="app-content"),
                    
                ],
                style={"height":"100%"}
            ),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

@dashapp.callback( 
    Output('app-content', 'children'),
    Output("download-session",'data'), 
    Output('saveas','data'),
    Input('url', 'pathname'),
    State('sortby', 'data'))
def make_app_content(pathname,sortby):

    # ctx = dash.callback_context
    # button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    # if button_id == "download-session" :
    #     return dcc.Location(pathname="/storage/", id='index'), dash.no_update

    user_id=str(current_user.id)
    users_data=app.config['USERS_DATA']
    user_path=os.path.join(users_data, user_id)

    if not os.path.isdir(user_path):
        os.makedirs(user_path)

    ui_path=pathname.split(f"{PAGE_PREFIX}/storage/", 1)[-1]

    saveas=False
    load=False
    download=False
    delete=False
    session_data=dash.no_update

    if ui_path :
        if ui_path[:len("load/")] == "load/":
            ui_path=ui_path.split("load/", 1)[-1]
            load=True

        elif ui_path[:len("download/")] == "download/":
            ui_path=ui_path.split("download/", 1)[-1]
            download=True

        elif ui_path[:len("delete/")] == "delete/":
            ui_path=ui_path.split("delete/", 1)[-1]
            delete=True

        elif ui_path[:len("saveas/")] == "saveas/":
            ui_path=ui_path.split("saveas/", 1)[-1]
            saveas=True
            if "session_data" in list( session.keys() ) :
                session_data = session["session_data"]
                del(session["session_data"])

    if ( ui_path ):
        if ( not download ) & ( not load ) & ( not delete ):
            if ui_path[-1] != "/":
                ui_path=f'{ui_path}/'

    os_path=os.path.join(user_path, ui_path)

    if load : 
        if not os.path.isfile(os_path):
            return dcc.Location(pathname=f'{PAGE_PREFIX}/storage/', refresh=True, id='index'), dash.no_update, session_data
        session_data=encode_session_file(os_path, current_user )
        load_app=session_data["app_name"]
        session["session_data"]=session_data
        from time import sleep
        sleep(2)
        return dcc.Location(pathname=f"{PAGE_PREFIX}/{load_app}/", id='index'), dash.no_update, session_data

    if download : 
        if not os.path.isfile( os_path ):
            return dcc.Location(pathname=f'{PAGE_PREFIX}/storage/', refresh=True, id='index'), dash.no_update, session_data
        ui_path=ui_path.split( os.path.basename(os_path) )[0]
        ui_path=f'{PAGE_PREFIX}/storage/{ui_path}'
        return dcc.Location(pathname=ui_path, refresh=True, id='index'), dcc.send_file( os_path ), session_data

    if delete : 
        if not os.path.exists( os_path ):
            return dcc.Location(pathname=f'{PAGE_PREFIX}/storage/', refresh=True, id='index'), dash.no_update, session_data
        if os.path.isdir(os_path):
            shutil.rmtree(os_path)
        if os.path.isfile(os_path):
            os.remove(os_path)

        ui_path="/".join( ui_path.split("/")[:-1] )
        ui_path=f'{PAGE_PREFIX}/storage/{ui_path}'

        return dcc.Location(pathname=ui_path, refresh=True, id='index'), dash.no_update, session_data

    if not os.path.isdir( os_path ):
        return dcc.Location(pathname=f"{PAGE_PREFIX}/storage/", id='index'), dash.no_update, session_data

    ### demo dev section
    # def touch_file(filepath):
    #     print(filepath)
    #     with open(filepath, "w") as f:
    #         f.write("test")
    # if not os.path.isdir(f'{os_path}test_dir/test_subdir'):
    #     os.makedirs(f'{os_path}test_dir/test_subdir')
    # for i in range(100) :
    #     touch_file(f'{os_path}test.file.{i}.json')
    # touch_file(f'{os_path}test_dir/test.file.2.json')
    # touch_file(f'{os_path}test_dir/test_subdir/test.file.3.json')
    # touch_file(f'{os_path}test_dir/test_subdir/test.file.4.json')
    ### 

    total_user=get_size(user_path)
    user=User.query.filter_by(id=current_user.id).first()
    disk_quota=user.disk_quota
    disc_per=total_user/disk_quota*100

    if disc_per < 1:
        disc_per=1

    if disc_per > 75:
        progress_color="danger"
    elif disc_per > 50:
        progress_color="warning"
    else:
        progress_color="success"

    if disc_per >= 30 :
        prog_label=f'{humanize.naturalsize(total_user)}/{humanize.naturalsize(disk_quota)}'
    elif disc_per >= 5 :
        prog_label=f'{disc_per}%'
    else:
        prog_label=""

    def make_icon(icon, href):
        # if PAGE_PREFIX:
        #     href=f'{PAGE_PREFIX}/{href}'
        ic=dcc.Link(
            [
                html.I(className=icon)
            ],
            href=href,
            refresh=True
        )
        return ic

    ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
    hide_dotfile="yes"
    contents = {}
    contents_df=pd.DataFrame(columns=['Name',"mod",'Modified','type','original_size','Size',\
        "path","ui_path","Delete","Load","Download"])
    total = {'size': get_size(os_path), 'dir': 0, 'file': 0}
    for filename in os.listdir(os_path):
        if filename in ignored:
            continue
        if hide_dotfile == 'yes' and filename[0] == '.':
            continue
        filepath = os.path.join(os_path, filename)
        stat_res = os.stat(filepath)
        info = {}
        info['Name'] = filename
        info["mod"]=stat_res.st_mtime
        info['Modified'] = time_humanize(stat_res.st_mtime)
        ft = get_type(stat_res.st_mode)
        info['type'] = ft
        total[ft] += 1
        sz = stat_res.st_size
        total['size'] += sz
        info['original_size']=sz
        info['Size']=humanize.naturalsize(sz)
        info["path"] = filepath
        info["ui_path"] = os.path.join(ui_path, filename)
        info["Delete"] = os.path.join("delete", ui_path, filename)
        info["Load"] = os.path.join("load", ui_path, filename)
        info["Download"] = os.path.join("download", ui_path, filename)
        info_df=pd.DataFrame(info,index=[0])
        contents[filename]=info
        contents_df=pd.concat([contents_df,info_df])
        
    contents_df.reset_index(inplace=True, drop=True)

    finder_data={ "contents":contents, "contents_df":contents_df.to_json(), "user_path":user_path }

    finder=make_finder(contents, contents_df, sortby, user_path)

    if not ui_path:
        home_active=True
    else:
        home_active=False

    home_path=f"{PAGE_PREFIX}/storage/"
    if saveas :
        home_path=f'{home_path}/{saveas}/'

    full_paths=[{"label": "Home", "href": home_path, "external_link": False, "active": home_active }]
    for p in ui_path.split("/")[:-1] :
        p_=full_paths[-1]["href"]
        p_=os.path.join(p_,p)
        if f'{p_}/' ==  f'{home_path}{ui_path}' :
            p_={"label": p, "external_link": False, "active": True }
        else:
            p_={"label": p, "href": p_, "external_link": False, "active": False }    
        full_paths.append(p_)

    if saveas:
        save_and_make=dbc.Row(
            [
                dbc.Col(dbc.Button("Save", color="secondary", id="saveas-btn"), width='auto'),
                dbc.Col(
                    dbc.Input(type="text", placeholder="filename", id="saveas_filename"),
                    className="me-2",
                ),
                dbc.Col(dbc.Button("Make", color="secondary", id="mkdir-btn"), width='auto'),
                dbc.Col(
                    dbc.Input(type="text", placeholder="dir name", id="makedir_dirname"),
                    className="me-2",
                    style={"left-margin":"40px" }
                ),
            ],
            className="g-1",
            style={"height": "30px",'margin-bottom':"24px",'margin-top':"0px"},
            justify="start"
        )
        upload_file_style={
            'width': '100%',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            "margin-bottom": "10px",
            'display': 'none'
        }
    else:
        save_and_make=dbc.Row(
            [
                dbc.Col(dbc.Button("Save", color="secondary", id="saveas-btn"), width='auto',style={'display': 'none'}),
                dbc.Col(
                    dbc.Input(type="text", placeholder="filename", id="saveas_filename"),
                    className="me-2",
                    style={'display': 'none'}
                ),
                dbc.Col(dbc.Button("Make", color="secondary", id="mkdir-btn"), width='auto'),
                dbc.Col(
                    dbc.Input(type="text", placeholder="dir name", id="makedir_dirname"),
                    # className="me-2",
                    width=5
                ),
                
            ],
            className="g-1",
            style={"height": "30px",'margin-bottom':"24px",'margin-top':"0px"},
            justify="end"
        )
        upload_file_style={
            'width': '100%',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            "margin-bottom": "10px",
        }

    page=html.Div(
        [   dcc.Store( data=finder_data, id='finder-data' ),
            dbc.Row( 
                [
                    dbc.Col( 
                        [ 
                            dbc.Progress(label=prog_label, value=disc_per, color=progress_color, style={"height": "30px",'margin-bottom':"14px",'margin-top':"80px"}),
                            dbc.Breadcrumb( items=full_paths,style={"height": "30px",'margin-bottom':"8px",'margin-top':"14px"}),
                            save_and_make,
                            dcc.Upload(
                                id='upload-data',
                                children=html.Div(
                                    [ html.A('upload a session file',id='upload-data-text') ],
                                    style={ 'textAlign': 'center', "margin-top": 4, "margin-bottom": 4}
                                ),
                                style=upload_file_style,
                                multiple=False,
                            ),
                            html.Div( 
                                finder,
                                id="finder-div",
                                style={"overflow":"scroll", "height":"100%"}
                            )
                        ],
                        sm=12,md=12, lg=10, xl=8, 
                        align="top", 
                        style={ "margin-left":2, "margin-right":2 ,'margin-bottom':"50px"}
                    ),
                ],
                align="top",
                justify="center",
                style={"min-height": "95vh", 'verticalAlign': 'center',"padding":"2px"}
            )
        
        ]

    )
    return page, dash.no_update, session_data

@dashapp.callback(
    Output('sortby', 'data'),
    Output('finder-div', 'children'),
    Input('finder-name', 'n_clicks'),
    Input('finder-size', 'n_clicks'),
    Input('finder-modified', 'n_clicks'),
    State('finder-data', 'data'),
    State('sortby', 'data'),
    prevent_initial_call=True
)
def update_table( f_name, f_size, f_modified, finder_data, sortby):

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == 'finder-name' :
        if  not f_name :
            return dash.no_update, dash.no_update
    elif button_id == 'finder-size' :
        if not f_size :
            return dash.no_update, dash.no_update
    elif button_id == 'finder-modified' :
        if not f_modified :
            return dash.no_update, dash.no_update

    buttons_dic={'finder-name':'Name',
        'finder-size':'original_size',
        'finder-modified':'mod'
    }

    new_sortby=buttons_dic[button_id]

    contents=finder_data["contents"]
    contents_df=pd.read_json(finder_data["contents_df"])
    user_path=finder_data["user_path"]
    if sortby:
        old_sortby=list(sortby.keys())[0]
        old_sortby_type=sortby[old_sortby]
    else:
        old_sortby=None

    if new_sortby == old_sortby:
        if old_sortby_type == "ascending" :
            new_sortby_type="descending"
        else:
            new_sortby_type="ascending"
    else:
        new_sortby_type="ascending"

    sortby_={new_sortby:new_sortby_type}

    finder=make_finder(contents, contents_df, sortby_, user_path)

    return sortby_, finder

@dashapp.callback(
    Output( "mkdir-refresh", "children" ),
    Output( 'url', 'pathname' ),
    Input( "mkdir-btn", "n_clicks" ),
    Input( "saveas-btn", "n_clicks" ),
    Input('upload-data', 'contents'),
    Input('upload-data', 'filename'),
    Input('upload-data', 'last_modified'),
    State( "makedir_dirname", "value"),
    State( "saveas_filename", "value"),
    State( 'saveas', 'data'),
    State( 'url', 'pathname' ),
    prevent_initial_call=True
)
def saveas_makedir(mkdir_n,saveas_n,  contents, upload_filename, last_modified, dirname, filename, session_data, pathname):

    ctx = dash.callback_context
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if button_id == "upload-data"  :
        if upload_filename : 

            user_id=str(current_user.id)
            users_data=app.config['USERS_DATA']
            user_path=os.path.join(users_data, user_id)

            if not os.path.isdir(user_path):
                os.makedirs(user_path)

            ui_path=pathname.split(f"{PAGE_PREFIX}/storage/", 1)[-1]

            os_path=os.path.join( user_path, ui_path )

            upload_filename=secure_filename(str(upload_filename))
            if upload_filename.split(".")[-1] != "json":
                upload_filename=f'{upload_filename}.json'  

            os_path=os.path.join(os_path, upload_filename )

            if os.path.exists(os_path):
                mod=dbc.Modal(
                    [
                        dbc.ModalHeader("Session upload"), 
                        dbc.ModalBody(
                            [
                                "File name already exists. Please delete file first."
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="dirname-close", color="secondary", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="dirname-modal",
                    is_open=True,
                )
                return mod, dash.no_update

            ## validate session file
            failed_upload_modal=dbc.Modal(
                [
                    dbc.ModalHeader("Session upload"), 
                    dbc.ModalBody(
                        [
                            "Not a valid session file."
                        ]
                    ),
                    dbc.ModalFooter(
                        dbc.Button(
                            "Close", id="dirname-close", color="secondary", className="ms-auto", n_clicks=0
                        )
                    ),
                ],
                id="dirname-modal",
                is_open=True,
            )
            try:
                content_type, content_string = contents.split(',')
                decoded=base64.b64decode(content_string)
                decoded=decoded.decode('utf-8')
                session_import=json.loads(decoded)
                print(type(session_import))
                keys = list(session_import.keys())
                for k in ["APP_VERSION","session_data"]:
                    if k not in keys:
                        return  failed_upload_modal, dash.no_update
                if "app" not in list(session_import["session_data"].keys()) :
                    return  failed_upload_modal, dash.no_update
            except:
                return  failed_upload_modal, dash.no_update
            
            with open(os_path, "w") as file_out:
                json.dump(session_import, file_out)

            return  dash.no_update, pathname


    if saveas_n :
        if button_id == "saveas-btn" :
            if not filename :
                dirname_modal=dbc.Modal(
                    [
                        dbc.ModalHeader("File name"), 
                        dbc.ModalBody(
                            [
                                "Please type in a file name before pressing 'Save'."
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="dirname-close", color="secondary", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="dirname-modal",
                    is_open=True,
                )

                return  dirname_modal, dash.no_update
            
            if not session_data :
                dirname_modal=dbc.Modal(
                    [
                        dbc.ModalHeader("Session data"), 
                        dbc.ModalBody(
                            [
                                "Could not find any data to save."
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="dirname-close", color="secondary", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="dirname-modal",
                    is_open=True,
                )

                return  dirname_modal, dash.no_update

            
            user_id=str(current_user.id)
            users_data=app.config['USERS_DATA']
            user_path=os.path.join(users_data, user_id)

            if not os.path.isdir(user_path):
                os.makedirs(user_path)

            ui_path=pathname.split(f"{PAGE_PREFIX}/storage/", 1)[-1]

            if ui_path[:len("saveas/")] == "saveas/":
                ui_path=ui_path.split("saveas/", 1)[-1]

            os_path=os.path.join( user_path, ui_path )

            filename=secure_filename(filename)
            if filename.split(".")[-1] != "json":
                filename=f'{filename}.json'  

            os_path=os.path.join(os_path, filename )

            with open(os_path, "w") as file_out:
                json.dump(session_data, file_out)

            return dash.no_update, f'{PAGE_PREFIX}/storage/{ui_path}'

    if  mkdir_n :
        if button_id == "mkdir-btn" :
            if not dirname :
                dirname_modal=dbc.Modal(
                    [
                        dbc.ModalHeader("Directory name"), 
                        dbc.ModalBody(
                            [
                                "Please type in a directory name before pressing 'Make'."
                            ]
                        ),
                        dbc.ModalFooter(
                            dbc.Button(
                                "Close", id="dirname-close", color="secondary", className="ms-auto", n_clicks=0
                            )
                        ),
                    ],
                    id="dirname-modal",
                    is_open=True,
                )

                return  dirname_modal, dash.no_update
           
            user_id=str(current_user.id)
            users_data=app.config['USERS_DATA']
            user_path=os.path.join(users_data, user_id)

            if not os.path.isdir(user_path):
                os.makedirs(user_path)

            ui_path=pathname.split(f"{PAGE_PREFIX}/storage/", 1)[-1]

            if ui_path[:len("saveas/")] == "saveas/":
                ui_path=ui_path.split("saveas/", 1)[-1]

            os_path=os.path.join( user_path, ui_path )

            dirname=secure_filename(dirname)

            os_path=os.path.join(os_path, dirname )

            if not os.path.isdir(os_path):
                os.makedirs(os_path)

            return dash.no_update, pathname

    return dash.no_update, dash.no_update


@dashapp.callback(
    Output('dirname-modal', 'is_open'),
    [ Input('dirname-close',"n_clicks")],
    [ State("dirname-modal", "is_open")], 
    prevent_initial_call=True
)
def dirname_modal_handle(n1, is_open):
    if n1 :
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