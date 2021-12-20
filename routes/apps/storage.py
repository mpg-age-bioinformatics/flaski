from myapp import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import parse_import_json, parse_table, make_options, make_except_toast, ask_for_help, save_session, load_session
import os
import uuid
import traceback
import json
import pandas as pd
import time
from werkzeug.utils import secure_filename
import humanize
from myapp.models import User
import stat
from datetime import datetime



FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("storage",url_base_pathname='/storage/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
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

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    protected_content=html.Div(
        [
            make_navbar_logged("Storage",current_user),
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
    user_id=str(current_user.id)
    users_data=app.config['USERS_DATA']
    user_path=os.path.join(users_data, user_id)
    ui_path=pathname.split("/storage/", 1)[-1]
    ui_path=ui_path.split("saveas/", 1)[-1]
    if ui_path:
        if ui_path[-1] != "/":
            ui_path=f'{ui_path}/'
    os_path=user_path+ui_path

    #if not os.path.isdir(os_path):
        ## issue
        ## redirect to os_path

    ### demo dev section
    def touch_file(filepath):
        with open(filepath, "w") as f:
            f.write("test")
    if not os.path.isdir(f'{user_path}/test_dir/test_subdir'):
        os.makedirs(f'{user_path}/test_dir/test_subdir')
    touch_file(f'{user_path}test.file.1.json')
    touch_file(f'{user_path}test_dir/test.file.2.json')
    touch_file(f'{user_path}test_dir/test_subdir/test.file.3.json')
    ### 

    if not os.path.isdir(user_path):
        os.makedirs(user_path)
    total_user=get_size(user_path)
    user=User.query.filter_by(id=current_user.id).first()
    disk_quota=user.disk_quota
    disc_per=total_user/disk_quota*100
    # print(disc_per)
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
        ic=dcc.Link(
            [
                html.I(className=icon)
            ],
            href=href,
            refresh=True
        )
        return ic

    # https://dash-bootstrap-components.opensource.faculty.ai/docs/components/breadcrumb/

    ignored = ['.bzr', '$RECYCLE.BIN', '.DAV', '.DS_Store', '.git', '.hg', '.htaccess', '.htpasswd', '.Spotlight-V100', '.svn', '__MACOSX', 'ehthumbs.db', 'robots.txt', 'Thumbs.db', 'thumbs.tps']
    hide_dotfile="yes"
    contents = {}
    contents_df=pd.DataFrame()
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
        info['Modified'] = time_humanize(stat_res.st_mtime)
        ft = get_type(stat_res.st_mode)
        info['type'] = ft
        total[ft] += 1
        sz = stat_res.st_size
        total['size'] += sz
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

    files=os.listdir(user_path)

    icons={"Delete":"fas fa-trash-alt","Load":"fas fa-spinner", "Download": "fas fa-file-download"}
    def make_icon(field, filename,ft=['dir','file'],contents=contents, icons=icons):
        info=contents[filename]
        if info["type"] in ft:
            ic=dcc.Link(
                [
                    html.I(className=icons[field])
                ],
                href=info[field],
                refresh=True
            )
        else:
            ic=""
        return ic


    def make_dir_links(filename,contents=contents):
        info=contents[filename]
        if info["type"] == "dir":
            dl=dcc.Link(
                [
                    filename
                ],
                href=info['ui_path'],
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

    contents_df=dbc.Table.from_dataframe(contents_df, striped=True, bordered=False, hover=True)

    finder=dbc.Card(
        dbc.Form(
            [ 
                #html.H2("tmp-files-table", style={'textAlign': 'center'} ),
                #"\n".join( files ),
                contents_df
            ]
        ),
        body=False,
        style={"overflow":"scroll"}
    )

    page=dbc.Row( 
        [
            dbc.Col( 
                [ 
                    dbc.Progress(label=prog_label, value=disc_per, color=progress_color, style={"height": "30px",'margin-bottom':"8px"}),

                    finder
                ],
                sm=12,md=12, lg=10, xl=8, 
                align="center", 
                style={ "margin-left":2, "margin-right":2 ,'margin-bottom':"50px","overflow":"scroll"}
            ),
        ],
        align="center",
        justify="center",
        style={"min-height": "95vh", 'verticalAlign': 'center',"padding":"2px"}
    )
    return page
    