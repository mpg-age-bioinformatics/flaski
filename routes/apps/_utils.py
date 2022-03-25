import io
import os
import json
import base64
import tempfile
import pandas as pd
import dash_bootstrap_components as dbc
from dash import dcc, html
import traceback
from myapp.email import send_email
from myapp import app
from datetime import datetime
from flask import render_template
from dash import dash_table

def parse_import_json(contents,filename,last_modified,session_id,cache,appname):
    # @cache.memoize(timeout=3600)
    def _parse_import_json(contents,filename,last_modified,session_id,cache,appname):
        content_type, content_string = contents.split(',')
        decoded=base64.b64decode(content_string)
        decoded=decoded.decode('utf-8')
        session_import=json.loads(decoded)

        # with open("/myapp_data/users/test.json", 'w') as f:
        #     json.dump(session_import, f)

        # # ENCODING EXAMPLE
        # dumped=json.dumps(session_import)
        # encoded=base64.b64encode(dumped.encode('utf-8'))
        # encoded=encoded.decode('utf-8')
        # contents=f'data:application/json;base64,{encoded}'
        # with open("/myapp_data/users/test.str", "w") as f:
        #     f.write(contents)

        # with open("/myapp_data/users/test.str", "r") as f:
        #     contents=f.readlines()[0]
        # print("A", contents[:200])

        session_import=session_import["session_data"]["app"][appname]

        return session_import
    return _parse_import_json(contents,filename,last_modified,session_id,cache,appname)

def parse_table(contents,filename,last_modified,session_id,cache,appname):
    # @cache.memoize(timeout=3600)
    def _parse_table(contents,filename,last_modified,session_id,cache):
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        extension=filename.split(".")[-1]
        if extension == 'csv':
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))
        elif extension == 'tsv':
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')), sep="\t")
        elif extension in ['xls', "xlsx"] :
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
            df = df.astype(str)
        return df.to_json()
    if filename.split(".")[-1] == "json" :
        import_json=parse_import_json(contents,filename,last_modified,session_id,cache,appname)
        df=import_json["df"]
        return pd.read_json(df)
    return pd.read_json(_parse_table(contents,filename,last_modified,session_id,cache))

def make_options(valuesin):
    opts=[]
    for c in valuesin:
        opts.append( {"label":c, "value":c} )
    return opts


def check_user_path(filename,current_user) :
    user_id=str(current_user.id)
    users_data=app.config['USERS_DATA']
    user_path=os.path.join(users_data, user_id)
    user_path=f'{user_path}/'
    if user_path == filename[:len(user_path)] :
        file_path = filename.split(user_path)[-1]
        if not os.path.isdir(user_path):
            os.makedirs(user_path)
    else:
        file_path=None
    return user_path, file_path

def make_save_toast(filename,id, header="Save"):
    toast=dbc.Toast( f'{filename}',
        id={'type':'toast-error','index':id},
        header=header,
        is_open=True,
        dismissable=True,
        icon="success",
        duration=1900,
        # top: 66 positions the toast below the navbar
        # style={"position": "fixed", "z-index": 0, "top": 66, "right": 10, "width": 350,},
    )
    return toast

def save_session(session_data, filename,current_user, func ):
    if filename.split(".")[-1] == "json" :
        ## check that path is user path
        user_path, file_path= check_user_path(filename,current_user)
        if file_path :
            with open(filename,"w") as json_file:
                json.dump(session_data, json_file)
            toast=make_save_toast(file_path,func)
        else:
            raise Exception("Target does not belong to user.")
    else:
        raise Exception("Not a session file.")
    return toast

def load_session( filename,current_user ):
    if filename.split(".")[-1] == "json" :
        ## check that path is user path
        user_path, file_path= check_user_path(filename,current_user)
        if file_path :
            with open(filename,"r") as json_file:
                session_data=json.load( json_file )
            # toast=make_save_toast(file_path,func,header="Load")
        else:
            raise Exception("Target does not belong to user.")
    else:
        raise Exception("Not a session file.")

    return session_data

def encode_session_file(filename, current_user ):
    session_import=load_session( filename, current_user )
    session_data=session_import["session_data"]
    app_data=session_data["app"]
    app_name=list(app_data.keys())[0]
    last_modified=app_data[app_name]["last_modified"]
    session_import=json.dumps(session_import)
    session_import=base64.b64encode(session_import.encode('utf-8'))
    session_import=session_import.decode('utf-8')
    session_import=f'data:application/json;base64,{session_import}'
    return { "session_import":session_import, "last_modified":last_modified, "app_name":app_name, "sessionfilename": filename }

def encode_session_app(session_data):
    app_data=session_data["app"]
    app_name=list(app_data.keys())[0]
    last_modified=app_data[app_name]["last_modified"]
    filename=app_data[app_name]["filename"]
    session_import=json.dumps(session_data)
    session_import=base64.b64encode(session_import.encode('utf-8'))
    session_import=session_import.decode('utf-8')
    session_import=f'data:application/json;base64,{session_import}'
    return { "session_import":session_import, "last_modified":last_modified, "app_name":app_name, "sessionfilename": filename }


def make_except_toast(text=None,id=None,e=None,user=None, eapp=None):
    if e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))

        emsg_html=tb_str.split("\n")
        send_email(
            '[Flaski] exception: %s ' %eapp,
            sender=app.config['MAIL_USERNAME'],
            recipients=app.config['ADMINS'],
            text_body=render_template(
                'email/app_exception.txt',
                user=user, 
                eapp=eapp, 
                emsg=tb_str, 
                etime=str(datetime.now())
            ),
            html_body=render_template(
                'email/app_exception.html',
                user=user, 
                eapp=eapp, 
                emsg=emsg_html, 
                etime=str(datetime.now())
            ),
            reply_to=user.email 
        )

        text=[ text,
            dcc.Markdown(f'```{e}```'),
            "Something went wrong, we have been notified. If you would like to share your session with us and get help on this issue please press 'Ice Cream'.",
            dbc.Collapse(
                dbc.Card(
                    dbc.CardBody(
                        dcc.Markdown(f'```{tb_str}```'),
                    ),
                    color="light",
                ),
                id={'type':'collapse-toast-traceback','index':id},
                is_open=False,
                style={"margin-top":"10px","margin-bottom":"10px"}
            )
        ]
        is_open=True
    else:
        text=[]
        is_open=False


    toast=dbc.Toast( text+
        [
            html.Div(
                [
                    dbc.Button("expand", outline=True, color="dark",id={'type':'toggler-toast-traceback','index':id},size="sm", style={"margin-right":"2px"} ),
                    dbc.Button("Ice Cream", outline=True, color="dark",id={'type':'help-toast-traceback','index':id},size="sm", style={"margin-left":"2px"} )
                ],
                className="d-grid gap-2 d-md-flex justify-content-md-end",
                style={"margin-top":"10px"} 
            ),
        ],
        id={'type':'toast-error','index':id},
        header="Exception",
        is_open=is_open,
        dismissable=True,
        icon="danger",
        # top: 66 positions the toast below the navbar
        # style={"position": "fixed", "z-index": 0, "top": 66, "right": 10, "width": 350,},
    )
    return toast

def ask_for_help(tb_str, user, current_app, session_data=None ):
    
    if session_data:
        session_data=session_data["session_data"]
        share_folder=os.path.join(app.config["USERS_DATA"], 'shared_sessions')
        if not os.path.isdir(share_folder):
            os.makedirs(share_folder)
        session_file=tempfile.NamedTemporaryFile(dir=share_folder, suffix=".ses")
        with open(session_file,"w") as fout:
            json.dump(session_data, fout)
    else:
        session_file="no session file for this Exception"

    send_email('[Flaski] help needed: %s ' %current_app,
        sender=app.config['MAIL_USERNAME'],
        recipients=app.config['ADMINS'],
        text_body=render_template('email/app_help.txt',
                                    user=user, eapp=current_app, emsg=tb_str, etime=str(datetime.now()), session_file=session_file),
        html_body=render_template('email/app_help.html',
                                    user=user, eapp=current_app, emsg=tb_str.split("\n"), etime=str(datetime.now()), session_file=session_file),\
        reply_to=user.email )      

def make_min_width(x, factor=7):
    name_length = len(x)
    pixel = 50 + round(name_length*7)
    pixel = str(pixel) + "px"


def make_table(df,id,page_size=50,fixed_columns=False):

    def create_conditional_style(df):
        style=[]
        for col in df.columns:
            pixel=make_min_width(col, factor=7)
            # name_length = len(col)
            # pixel = 50 + round(name_length*7)
            # pixel = str(pixel) + "px"
            style.append({'if': {'column_id': col}, 'minWidth': pixel})

        return style
    # width_style=create_conditional_style(df)
    width_style=[]
    # print(width_style)
    
    report_table=dash_table.DataTable(
        id=id,
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        fixed_rows={ 'headers': True, 'data': 0 },
        fixed_columns=fixed_columns, 
        style_cell={
            'whiteSpace': 'normal'
        },
        virtualization=True,
        style_table={"height": "100%", 'width':"100%",'overflowY': 'auto', 'overflowX': 'auto','border': '1px solid rgb(223,223,223)'},
        style_header={'backgroundColor': '#5474d8','color': 'white','fontWeight': 'bold'},
        style_data_conditional=[
        { 'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(242,242,242)'}
        ]+width_style,
        page_size=page_size
        # page_action='none'
        )

    return report_table

