import sys
import dash_html_components as html
import dash_bootstrap_components as dbc
import traceback
import pandas as pd
import base64
import io
from flask_login import login_required
from flask import session
from flaski.routines import check_session_app
import traceback
from flaski.email import send_exception_email
from datetime import datetime
import dash_table

META_TAGS=[{'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'} ]

def make_options(valuesin):
    opts=[]
    for c in valuesin:
        opts.append( {"label":c, "value":c} )
    return opts

def handle_dash_exception(e, user, current_app):
    err = ''.join(traceback.format_exception(None, e, e.__traceback__))
    send_exception_email( user=user, eapp=current_app, emsg=err, etime=str(datetime.now()) )
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
    card_text=dbc.Card( card_text, body=True, color="gray", inverse=True) 
    return card_text

def parse_table(contents,filename,last_modified,session_id,cache):
    @cache.memoize(timeout=3600)
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
        return df.to_json()
    return pd.read_json(_parse_table(contents,filename,last_modified,session_id,cache))

def validate_user_access(current_user, app):
    # @cache.memoize(300)
    def check_current_user(current_user,app):
        apps=current_user.user_apps
        if app not in [ s["link"] for s in apps ] :
            return False
        reset_info=check_session_app(session,app,apps)
        if reset_info:
            # flash(reset_info,'error')
            session["app"]=app
        return True
    return check_current_user(current_user,app)

def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])

def make_navbar(app_name, current_user, cache):
    @cache.memoize(300)
    def _make_navbar(app_name, current_user):
        image_filename = '/flaski/flaski/static/dog-solid-white.png' # replace with your own image
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())

        logout_link=html.A("Logout", style={"vertical-align":"center", \
                                            'textAlign': 'center',\
                                            "margin-bottom":0, \
                                            "margin-top":8, \
                                            # "margin-left":6, \
                                            # "margin-right":6
                                            "color":"#acbae8",}, href="/logout")

        separator=html.A("", style={"font-size":"25px",
        "margin-left":8,
        "margin-right":8,  
        "margin-bottom":4,
        "margin-top":0,
        "align":"center", 
        "color":"#acbae8"})

        apps=current_user.user_apps

        dropdown_items=[]
        for a in apps :
            i=dbc.DropdownMenuItem(a['name'], href="/%s" %str(a['link']), external_link=True)
            dropdown_items.append(i)

        dropdown=dbc.DropdownMenu(
                    children=dropdown_items,
                    nav=True,
                    in_navbar=True,
                    label="Apps",
                    right=True,
                    style={ "align":"center"}
                )

        inner_brand_col=html.A(
                        dbc.Row(
                            [                         
                                dbc.Col( html.A( html.Img( src='data:image/png;base64,{}'.format(encoded_image.decode()) , height="30px", style={ "margin-bottom":5}), href="/index")),
                                dbc.Col( dbc.NavbarBrand("Flaski.Dash  |  %s" %str(app_name), className="ml-2") ),
                                dbc.Col( dbc.NavbarToggler(id="navbar-toggler", className="ml-auto" ))
                            ],
                            align="center",
                            no_gutters=True,
                        )
                    )
 
        brand=dbc.Col(inner_brand_col , width=True, style={ 'textAlign': 'center'}) # sm=6, md=6,
        brand_=dbc.Col(dbc.NavbarBrand(app_name, href="#"), sm=3, md=6, style={ 'textAlign': 'left'})

        navbar = dbc.Navbar(
            dbc.Container(
                [
                    brand,
                    # brand_,
                    # dbc.NavbarToggler(id="navbar-toggler" ),
                    dbc.Collapse(
                        dbc.Nav(
                            [dropdown, separator, logout_link],
                            # dbc.Row([separator],style={"margin-left":8},align="center"), 
                            # dbc.Row([logout_link],style={"margin-left":8},align="center")], 
                            # [dbc.Row([dropdown],style={"margin-left":8},align="center"),
                            # dbc.Row([separator],style={"margin-left":8},align="center"), 
                            # dbc.Row([logout_link],style={"margin-left":8},align="center")], 
                            className="ml-auto", navbar=True
                        ),
                        id="navbar-collapse",
                        navbar=True,
                        is_open=False,
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
        return navbar
    return _make_navbar(app_name, current_user)

def make_footer():
    footer=[ html.Hr( style={"margin-top": 5, "margin-bottom": 5 } ),
    dbc.Row( 
        html.Footer( html.A("Iqbal, A., Duitama, C., Metge, F., Rosskopp, D., Boucas, J. Flaski. (2021). doi:10.5281/zenodo.4849515", 
            style={"color":"#35443f"},
            href="https://github.com/mpg-age-bioinformatics/flaski#citing"), 
        style={"margin-top": 5, "margin-bottom": 5, "margin-left": "20px"},
        ),
        style={"justify-content":"center"}
        )
    ]
    return footer

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

def change_table_minWidth(tb,minwidth):
    st=tb.style_table
    st["minWidth"]=minwidth
    tb.style_table=st
    return tb

def change_fig_minWidth(fig,minwidth):
    st=fig.style
    st["minWidth"]=minwidth
    fig.style=st
    return fig