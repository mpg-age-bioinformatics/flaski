from myapp import app, db, PAGE_PREFIX
import dash
from dash.dependencies import Input, Output, State
from dash import dcc, html
import dash_bootstrap_components as dbc
from myapp.models import User, PrivateRoutes
from myapp.email import send_validate_email
from datetime import datetime
from ._utils import META_TAGS, check_email, password_check, navbar_A, protect_dashviews, make_navbar_logged
from flask_login import current_user
from ._vars import other_nav_dropdowns, _PRIVATE_ROUTES, _PUBLIC_VIEWS

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("home",url_base_pathname=f'{PAGE_PREFIX}/home/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

dashapp.layout=html.Div( [ 
                dcc.Location(id='url', refresh=False),
                html.Div(id="protected-content"),
                ] 
            )

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    container_children=[]
    for o in other_nav_dropdowns :
        label= list(o.keys())[0]

        label_title=dbc.Row( 
            dbc.Col(
                [
                    html.H1(label, style={"font-size":"60px"} )
                ],
                align="center",
            ),
            align="center",
            justify="center",
            style={'textAlign':'center',"margin-top":"15%", "margin-bottom":"10%"}
        )

        container_children.append(label_title)

        links_dic=o[label]
        links_keys=list(links_dic.keys())
        i = 0
        row=[]
        for l in list( links_keys ) :
            app_route=links_dic[l].split("/")[1]
            if app_route in _PRIVATE_ROUTES :
                route_obj=PrivateRoutes.query.filter_by(route=app_route).first()
                if not route_obj :
                    continue
                users=route_obj.users
                uid=current_user.id
                if uid not in users :
                    continue
            l_=links_dic[l]
            link_icon=dbc.Col(
                [
                    dcc.Link(
                        [
                            html.I(className="fas fa-3x fa-flask", ),
                            html.H4(l, style={"textAlign":"center"} ),
                        ],
                        href=f'{PAGE_PREFIX}{l_}',
                        refresh=True,
                        style={"color":"black","text-decoration": "none"}
                    )                        
                ],
                align="center",
                xs=6, sm=3, md=3, lg=3,
                style={"margin-top":"40px", "margin-bottom":"40px"} 
            )
            
            row.append(link_icon)        
            i=i+1
            if i == 4:
                i=0
        if ( i != 0 ) & ( len(row) > 4 ):
            while i < 4:
                link_icon=dbc.Col(
                    [  ],
                    align="center",
                    xs=6, sm=3, md=3, lg=3,
                    style={"margin-top":"40px", "margin-bottom":"40px"} 
                )
                row.append(link_icon)
                i=i+1

        row=dbc.Row( 
            children=row,
            align="center",
            justify="evenly",
            style={'textAlign':'center'}
        )
        container_children.append(row)

    protected_content=html.Div(
        [
            dbc.Container(
                container_children,
                style={"min-height": "80vh"}
            ),
            navbar_A
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content


@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
    )
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open