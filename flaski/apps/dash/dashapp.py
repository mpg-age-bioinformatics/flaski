from flaski import app
from flask_login import current_user
from flask_caching import Cache
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from ._utils import handle_dash_exception, parse_table, protect_dashviews, validate_user_access
from ._dashapp import make_figure
import uuid

# import pandas as pd
import os
import base64

CURRENTAPP="dashapp"

dashapp = dash.Dash(CURRENTAPP,url_base_pathname=f'/{CURRENTAPP}/' , server=app, external_stylesheets=[dbc.themes.BOOTSTRAP])
protect_dashviews(dashapp)

cache = Cache(dashapp.server, config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), os.environ.get('REDIS_ADDRESS') )  #'redis://localhost:6379'),
})


image_filename = os.getcwd()+'/flaski/static/dog-solid-white.png' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())

dropdown=dbc.DropdownMenu(
            children=[
                dbc.DropdownMenuItem("Page 2", href="#"),
                dbc.DropdownMenuItem("Page 3", href="#"),
            ],
            nav=True,
            in_navbar=True,
            label="Apps",
            right=True
        )

inner_brand_col=html.A(
                dbc.Row(
                    [                         
                        html.Img( src='data:image/png;base64,{}'.format(encoded_image.decode()) , height="30px", style={ "margin-bottom":5}),
                        dbc.NavbarBrand("Flaski.Dash  |  Demo App", className="ml-2"),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="/index",
            )

brand=dbc.Col(inner_brand_col, sm=3, md=3, style={ 'textAlign': 'center'})
brand_=dbc.Col(dbc.NavbarBrand("Demo App", href="#"), sm=3, md=6, style={ 'textAlign': 'left'})

navbar = dbc.Navbar(
    dbc.Container(
        [
            brand,
            # brand_,
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ], 
    fluid=True,
    style={"margin-left":0,"margin-right":0, 'textAlign': 'center'}
    ),
    color="#5474d8",
    dark=True,
    # className="mb-5",
    style={"margin-bottom":10, "margin-left":0,"margin-right":0}
)
# )

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

side_bar=[ dbc.Card(controls, body=True),
            html.Button(id='submit-button-state', n_clicks=0, children='Submit', style={"width": "100%","margin-top":4} )
         ]
                        
# Define Layout
dashapp.layout = html.Div( [ navbar, dbc.Container(
    fluid=True,
    children=[
        html.Div(id="app_access"),
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dbc.Row(
            [
                dbc.Col( id="side_bar", md=3, style={"height": "100%",'overflow': 'scroll'} ),
                dbc.Col( id='my-output', md=9, style={"height": "100%","width": "100%",'overflow': 'scroll'})
            ], 
             style={"height": "87vh"}),
    ] ),
    html.Hr( style={"margin-top": 5, "margin-bottom": 5 } ),
    dbc.Row( 
        html.Footer( html.A("Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515", style={"color":"#35443f"},href="/"), 
        style={"margin-top": 5, "margin-bottom": 5, "margin-left": "20px"},
        ),
        style={"justify-content":"center"}
        )
]) 

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
    State('upload-data', 'last_modified')
)
def update_output(session_id, n_clicks, contents, x_col, multiplier, filename, last_modified):
    if not validate_user_access(current_user,CURRENTAPP,cache):
        return None
    if contents is not None:
        try:
            # df=get_dataframe(session_id,contents,filename,last_modified)
            df=parse_table(contents,filename,last_modified,session_id,cache)

            # demo purspose for multipliter value
            y=df.columns.tolist()[1]
            df["x"]=df[x_col].astype(float)
            df["y"]=df[y].astype(float)
            df["x"]= df["x"]*float(multiplier)

            fig=make_figure(df)
            fig=dcc.Graph(figure=fig)

        except Exception as e:
            fig=handle_dash_exception(e,current_user,CURRENTAPP)

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
    if not validate_user_access(current_user,CURRENTAPP,cache):
        return None
    if contents is not None:
        # df=get_dataframe(session_id,contents,filename,last_modified)
        df=parse_table(contents,filename,last_modified,session_id,cache)
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
    [dash.dependencies.Input('opt-xcol', 'options')] )
def set_xcol(available_options):
    if not validate_user_access(current_user,CURRENTAPP,cache):
        return None
    if available_options:
        return available_options[0]['value']

# this call back prevents the side bar from being shortly 
# show / exposed to users without access to this App
@dashapp.callback( Output('app_access', 'children'),
                   Output('side_bar', 'children'),
                   Input('session-id', 'data') )
def get_side_bar(session_id):
    if not validate_user_access(current_user,CURRENTAPP,cache):
        return dcc.Location(pathname="/index", id="index"), None
    else:
        return None, side_bar

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