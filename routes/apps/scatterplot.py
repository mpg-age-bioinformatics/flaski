from myapp import app
import dash
from myapp.routes._utils import META_TAGS, protect_dashviews
import dash_bootstrap_components as dbc
from dash import dcc, html

dashapp = dash.Dash("scatterplot",url_base_pathname='/scatterplot/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP], title=app.config["APP_TITLE"], assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/")

protect_dashviews(dashapp)

dashapp.layout=html.Div( 
    [ 
        dcc.Location(id='url', refresh=False),
        html.Div(id="app-redirect"),
        html.Div(id="protected-content"),
    ] 
)