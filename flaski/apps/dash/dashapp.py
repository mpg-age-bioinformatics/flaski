from flask import render_template, Flask, Response, request, url_for, redirect, session, send_file, flash, jsonify
from flaski import app
from werkzeug.utils import secure_filename
from flask_session import Session
from flaski.forms import LoginForm
from flask_login import current_user, login_user, logout_user, login_required
from datetime import datetime
from flaski import db
from werkzeug.urls import url_parse
from flaski.models import User, UserLogging
from flaski.email import send_exception_email
from flaski.routines import check_session_app, handle_exception, read_request, fuzzy_search
from flask_caching import Cache

import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

import uuid

import flask
import pandas as pd
import time
import os
import plotly.graph_objects as go

import traceback
import dash_html_components as html
import dash_bootstrap_components as dbc
import base64
import datetime
import io
import pandas as pd

def handle_error(e):
    err = ''.join(traceback.format_exception(None, e, e.__traceback__))
    err = err.split("\n")
    card_text= [ html.H4("Exception") ] 
    for s in err:
        s_=str(s)
        i=0
        if len(s_) > 0:
            while s_[0] == " ":
                i=i+1
                s_=s_[i:]
            i=i*10
            card_text.append(html.P(s, style={"margin-top": 0, "margin-bottom": 0, "margin-left": i}))
    fig=dbc.Card( card_text, body=True, color="gray", inverse=True) 
    return fig

def parse_table(contents,filename,last_modified):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    if 'csv' in filename:
        # Assume that the user uploaded a CSV file
        df = pd.read_csv(
            io.StringIO(decoded.decode('utf-8')))
    elif 'xls' in filename:
        # Assume that the user uploaded an excel file
        df = pd.read_excel(io.BytesIO(decoded)) 
    return df

def make_figure(df):
    fig = go.Figure( )
    fig.update_layout(  width=600, height=600)
    fig.add_trace(go.Scatter(x=df["x"].tolist(), y=df["y"].tolist() ))
    fig.update_layout(
            title={
                'text': "Demo plotly title",
                'xanchor': 'left',
                'yanchor': 'top' ,
                "font": {"size": 25, "color":"black"  } } )
    return fig

###### END OF UTILS ######

# standard make output function
def make_output(session_id,multiplier,contents,filename,last_modified,x_col):
    try:
        df=get_dataframe(session_id,contents,filename,last_modified)

        # demo purspose for multipliter value
        y=df.columns.tolist()[1]
        df["x"]=df[x_col].astype(float)
        df["y"]=df[y].astype(float)
        df["x"]= df["x"]*float(multiplier)

        fig=make_figure(df)
        fig=dcc.Graph(figure=fig)

    except Exception as e:
        fig=handle_error(e)
    return fig

dashapp = dash.Dash('dashapp',url_base_pathname='/dashapp/', server=app, external_stylesheets=[dbc.themes.BOOTSTRAP])

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
    # 'CACHE_REDIS_PASSWORD': os.environ.get('REDIS_PASSWORD', 'REDIS_PASSWORD')
})

def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])

_protect_dashviews(dashapp)

def get_dataframe(session_id, contents,filename,last_modified):
    @cache.memoize()
    def query_and_serialize_data(session_id, contents,filename,last_modified):
        df=parse_table(contents, filename, last_modified)
        return df.to_json()
    return pd.read_json(query_and_serialize_data(session_id,contents,filename,last_modified))


# app.scripts.config.serve_locally = False
# dcc._js_dist[0]['external_url'] = 'https://cdn.plot.ly/plotly-basic-latest.min.js'

controls = [ html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select File')], style={ 'textAlign': 'center', "margin-top": 3, "margin-bottom": 3} 
        ),
        style={
            'width': '100%',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
        },
        # Allow multiple files to be uploaded
        multiple=False
    )]),
    html.Label('X values', style={"margin-top":10}),
    dcc.Dropdown(
        id='opt-xcol',
    ),
    html.H5("Arguments", style={"margin-top":10}), 
    "X multiplier: ", dcc.Input(id='multiplier', value=1, type='text') ]

# Define Layout
dashapp.layout = dbc.Container(
    fluid=True,
    children=[
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        html.H2("A dash based web application for scatterplots.", style={"margin-top": 10}),
        html.Hr(),
        dbc.Row(
            [
                dbc.Col( [ dbc.Card(controls, body=True),
                html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%","margin-top":4} )]  ,  
                md=3, style={"height": "100%",'overflow': 'scroll'}),
                
                dbc.Col( id='my-output', md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"height": "87vh"}),
        html.Hr( style={"margin-top": 5, "margin-bottom": 5 } ),
        dbc.Row( html.Footer("Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing", style={"margin-top": 5, "margin-bottom": 5, "margin-left": "20px"}) )
    ],
    style={"margin": "auto", "height": "100vh"},
)

## all callback elements with `State` will be updated only once submit is pressed
## all callback elements wiht `Input` will be updated everytime the value gets changed 
@dashapp.callback(
    Output(component_id='my-output', component_property='children'),
    Input('session-id', 'data'),
    Input('submit-button-state', 'n_clicks'),
    State('upload-data', 'contents'),
    State("opt-xcol", "value"),
    State(component_id='multiplier', component_property='value'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified') )
def update_output(session_id,n_clicks,contents, x_col, multiplier,filename,last_modified):
    if contents is not None:
        fig=make_output(session_id,multiplier,contents,filename,last_modified,x_col)
        print(session,session["user_id"])
        import sys
        sys.stdout.flush()
        return fig

## update x-col options after reading the input file
@dashapp.callback(
    Output(component_id='opt-xcol', component_property='options'),
    Input('session-id', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified')
    )
def update_xcol(session_id,contents,filename,last_modified):
    if contents is not None:
        df=get_dataframe(session_id,contents,filename,last_modified)
        cols=df.columns.tolist()
        opts=[]
        for c in cols:
            opts.append( {"label":c, "value":c} )
    else:
        opts=[]
    return opts

## update x-col value once options are a available
@dashapp.callback(
    dash.dependencies.Output('opt-xcol', 'value'),
    [dash.dependencies.Input('opt-xcol', 'options')])
def set_xcol(available_options):
    if available_options:
        return available_options[0]['value']

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