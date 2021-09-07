import dash_html_components as html
import dash_bootstrap_components as dbc
import traceback
import pandas as pd
import base64
import io
from flask_login import login_required


def handle_dash_exception(e):
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
    card_text=dbc.Card( card_text, body=True, color="gray", inverse=True) 
    return card_text

def parse_table(contents,filename,last_modified,session_id,cache):
    @cache.memoize()
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
        print("doing it again")
        import sys
        sys.stdout.flush()
        return df.to_json()
    return pd.read_json(_parse_table(contents,filename,last_modified,session_id,cache))
    
def protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.config.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(
                dashapp.server.view_functions[view_func])