from myapp import app, db, PAGE_PREFIX
from flask_login import current_user
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import dash_bootstrap_components as dbc
from myapp.email import send_email
import os
from datetime import datetime, date
from myapp.routes._utils import META_TAGS, navbar_A
from flask import render_template
from myapp.models import User, FTPSubmissions
import pymysql.cursors
import shutil

dashapp = dash.Dash("transfer",url_base_pathname=f'{PAGE_PREFIX}/transfer/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

if app.config['PAGE_PREFIX'] == "" :
    home_page="/"
else:
    home_page=app.config['PAGE_PREFIX']

dashapp.layout=dbc.Row( 
    [
        dbc.Col( 
            [ 
                dcc.Location(id='url', refresh=False),
                dbc.Card(  
                    # dbc.Form(), 
                    id="release-form",
                    body=True
                ), 
            ],
            md=8, lg=6, xl=4, 
            align="center", 
            style={ "margin-left":2, "margin-right":2 ,'margin-bottom':"50px"}
        ),
        navbar_A
    ],
    align="center",
    justify="center",
    style={"min-height": "95vh", 'verticalAlign': 'center'}
)

@dashapp.callback(
    Output('release-form', 'children'),
    Input('url', 'pathname'))
def request_change( pathname):
    token=pathname.split("/transfer/")[-1]
    s_id=FTPSubmissions.verify_submission_token(token)
    if not s_id :
        request_form=dbc.Form(
           [ 
                html.H2("Error", style={'textAlign': 'center'} ),
                html.Div("Token could not be found.", style={'textAlign': 'center'})
            ]
        )
        return request_form

    s=FTPSubmissions.query.get(s_id)
    submission_file=s.file_name

    if not os.path.isfile(submission_file) :
        request_form=dbc.Form(
           [ 
                html.H2("Error", style={'textAlign': 'center'} ),
                html.Div("Submission could not be found.")
            ]
        )
        return request_form

    filename=os.path.basename(submission_file)

    request_form=dbc.Form(
        [ 
            html.H2("Submit request", style={'textAlign': 'center'} ),
            html.Div(f"Please make sure you have transfered all your files for your '{filename}' request before pressing 'Submit'."), 
            html.Div(
                dbc.Button("Submit", id='reset-button',color="secondary", n_clicks=0, className="me-1",style={"width":"auto","margin-top":10, "margin-bottom":4}),
                className="d-grid gap-2 d-md-flex justify-content-md-end",
            ),
            # html.Div(
            #     html.Button(id='reset-button', n_clicks=0, children='Submit', style={"width":"auto","margin-top":4, "margin-bottom":4}),
            #     style = { "margin-top":"10px"}
            # ),
            html.Div(id="submit-feedback") 
        ]
    )
    return request_form
    
@dashapp.callback(
    Output('submit-feedback', 'children'),
    Input('reset-button', 'n_clicks'),
    State('url', 'pathname'),
    prevent_initial_call=True )
def release_request(n_clicks, pathname):
    token=pathname.split("/transfer/")[-1]
    s_id=FTPSubmissions.verify_submission_token(token)
    s=FTPSubmissions.query.get(s_id)
    submission_file=s.file_name
    filename=os.path.basename(submission_file)
    dest=os.path.join("/mpcdf",filename)

    if not os.path.isfile(submission_file) :
        modal=dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Error",id="modal_header") ),
                dbc.ModalBody("Submission could not be found.", id="modal_body"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0, href=home_page
                    )
                ),
            ],
            id="modal",
            is_open=True,
        )
        return modal

    today=str(date.today())
    PUREFTPD_AUTH_SALT=os.getenv('PUREFTPD_AUTH_SALT')
    PUREFTPD_MYSQL_SERVER=os.getenv('PUREFTPD_MYSQL_SERVER')
    PUREFTPD_MYSQL_PORT=os.getenv('PUREFTPD_MYSQL_PORT')
    PUREFTPD_MYSQL_USER=os.getenv('PUREFTPD_MYSQL_USER')
    PUREFTPD_MYSQL_PASS=os.getenv('PUREFTPD_MYSQL_PASS')
    PUREFTPD_MYSQL_DB=os.getenv('PUREFTPD_MYSQL_DB')

    ftp_user=s.ftp_user

    try:
        connection = pymysql.connect(host=PUREFTPD_MYSQL_SERVER,
                                    port=int(PUREFTPD_MYSQL_PORT),
                                    user=PUREFTPD_MYSQL_USER,
                                    password=PUREFTPD_MYSQL_PASS,
                                    database=PUREFTPD_MYSQL_DB,
                                    ssl_ca='/etc/mysql/certs/ca-cert.pem',
                                    ssl_key='/etc/mysql/certs/client-key.pem',
                                    ssl_cert='/etc/mysql/certs/client-cert.pem',
                                    cursorclass=pymysql.cursors.DictCursor)

        with connection:
            with connection.cursor() as cursor:
                sql=( f"UPDATE users SET uploaded = {today} WHERE user = '{ftp_user}';" )  
                response=cursor.execute(sql)
            connection.commit()

    except:
        modal=dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Error",id="modal_header") ),
                dbc.ModalBody("ftp server could not be reached. Please try again later.", id="modal_body"),
                dbc.ModalFooter(
                    dbc.Button(
                        "Close", id="close", className="ms-auto", n_clicks=0, href=home_page
                    )
                ),
            ],
            id="modal",
            is_open=True,
        )
        return modal

    modal=dbc.Modal(
        [
            dbc.ModalHeader(dbc.ModalTitle("Success",id="modal_header") ),
            dbc.ModalBody("Your request has been released.", id="modal_body"),
            dbc.ModalFooter(
                dbc.Button(
                    "Close", id="close", className="ms-auto", n_clicks=0, href=home_page
                )
            ),
        ],
        id="modal",
        is_open=True,
    )

    submission_type=filename.split(".")[-2]

    user=User.query.get(s.user_id)

    shutil.move(submission_file, dest)

    xlsx_file=submission_file.replace(".json", ".xlsx")
    if os.path.isfile(xlsx_file) :
        shutil.move(xlsx_file, dest.replace(".json", ".xlsx"))

    submission_tag=os.path.basename(dest)

    send_email(f'[Flaski][Automation][{submission_type}] Files have been transfered.',
        sender=app.config['MAIL_USERNAME'],
        recipients=[user.email, 'automation@age.mpg.de' ], 
        text_body=render_template('email/submissions.ftp.data.txt',
                                    user=user, filename=os.path.basename(submission_tag), submission_tag=submission_tag, submission_type=submission_type),
        html_body=render_template('email/submissions.ftp.data.html',
                                    user=user, filename=os.path.basename(submission_tag), submission_tag=submission_tag, submission_type=submission_type),\
        reply_to='bioinformatics@age.mpg.de',\
        attachment=None ,
        attachment_path=None, 
        open_type="rb",\
        attachment_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    return modal