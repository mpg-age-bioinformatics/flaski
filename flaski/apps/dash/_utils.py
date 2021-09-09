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

def validate_user_access(current_user, app, cache):
    @cache.memoize(300)
    def check_current_user(current_user,app):
        apps=current_user.user_apps
        if "dashapp" not in [ s["link"] for s in apps ] :
            return False
        reset_info=check_session_app(session,app,apps)
        if reset_info:
            # flash(reset_info,'error')
            session["app"]="dashapp"
        return True
    return check_current_user(current_user,app)

def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])

def make_navbar(app_name, current_user):
    def _make_navbar(app_name, current_user):
        image_filename = '/flaski/flaski/static/dog-solid-white.png' # replace with your own image
        encoded_image = base64.b64encode(open(image_filename, 'rb').read())

        logout_link=html.A("Logout", style={"align":"center", "color":"#acbae8"},href="/logout")

        separator=html.A("|", style={"font-size":"25px",
        "margin-left":10,
        "margin-right":14,  
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
                    right=True
                )

        inner_brand_col=html.A(
                        dbc.Row(
                            [                         
                                html.Img( src='data:image/png;base64,{}'.format(encoded_image.decode()) , height="30px", style={ "margin-bottom":5}),
                                dbc.NavbarBrand("Flaski.Dash  |  %s" %str(app_name), className="ml-2"),
                            ],
                            align="center",
                            no_gutters=True,
                        ),
                        href="/index",
                    )

        brand=dbc.Col(inner_brand_col, sm=3, md=3, style={ 'textAlign': 'center'})
        brand_=dbc.Col(dbc.NavbarBrand(app_name, href="#"), sm=3, md=6, style={ 'textAlign': 'left'})

        navbar = dbc.Navbar(
            dbc.Container(
                [
                    brand,
                    # brand_,
                    dbc.NavbarToggler(id="navbar-toggler2"),
                    dbc.Collapse(
                        dbc.Nav(
                            [dbc.Row([dropdown, separator, logout_link],align="center")], 
                            className="ml-auto", navbar=True
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