from myapp import app, PAGE_PREFIX
from flask_login import current_user
from flask_caching import Cache
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from myapp.routes.apps._utils import check_access, make_submission_file
import os
import uuid
import tempfile
from glob import iglob
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import pandas as pd

from myapp import db
from myapp.models import UserLogging


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash("llms",url_base_pathname=f'{PAGE_PREFIX}/llms/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="LLMs",  assets_folder=app.config["APP_ASSETS"])# , assets_folder="/flaski/flaski/static/dash/") update_title='Load...', 

protect_dashviews(dashapp)

if app.config["SESSION_TYPE"] == "sqlalchemy":
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"] , echo=True)
    app.config["SESSION_SQLALCHEMY"] = engine
elif app.config["CACHE_TYPE"] == "RedisCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' %( os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS'] )  #'redis://localhost:6379'),
    })
elif app.config["CACHE_TYPE"] == "RedisSentinelCache" :
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [ 
            [ os.environ.get('CACHE_REDIS_SENTINELS_address'), os.environ.get('CACHE_REDIS_SENTINELS_port') ]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })

dashapp.layout=html.Div( 
    [ 
        dcc.Store( data=str(uuid.uuid4()), id='session-id' ),
        dcc.Location( id='url', refresh=True ),
        html.Div( id="protected-content" ),
    ] 
)


@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname'))
def make_layout(pathname):
    header_access, msg_access = check_access( 'llms' )
    if header_access :
        return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
    eventlog = UserLogging(email=current_user.email, action="visit llms")
    db.session.add(eventlog)
    db.session.commit()
    protected_content=html.Div(
        [
            make_navbar_logged("LLMs",current_user),
            html.Div(id="app-content"),
            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content

# Increment this version whenever the responsibility notice changes.
RESPONSIBILITY_NOTICE_VERSION = "2026-10-09.1"
RESPONSIBILITY_NOTICE = """
### Access to facility-hosted LLMs

This form requests an access key for large language models (LLMs) hosted by the
Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing
on a private server. Submitting a request does not automatically grant access
or issue a key; requests are subject to review by the facility. The service uses
open-source models, and the available models and versions may change over time.
The LLM endpoint is accessible only from within institutional networks.

### Your responsibility

You assume full responsibility for your use of the service, the prompts and data
you submit, any tools or external resources you connect, and any decisions,
actions, publications, or other outcomes based on model outputs. You must follow
applicable laws, institutional policies, data protection requirements, and
intellectual property rights. You must also follow any service-specific usage
rules communicated by the facility.

To the extent permitted by applicable law, neither the Bioinformatics Core
Facility of the Max Planck Institute for Biology of Ageing nor any of its members
accepts responsibility or liability for problems, losses, damage, or consequences
arising from your use of the service. This includes errors or vulnerabilities
inherent in the models, inaccurate or misleading outputs, bias, harmful content,
service interruptions, data loss or disclosure, and prompt injection or other
attacks encountered when accessing external websites, documents, or tools.
This acknowledgement does not exclude liability that cannot lawfully be excluded.

### Model limitations and verification

Models can invent facts, citations, code, and explanations, and may produce
confident but incorrect, incomplete, biased, or outdated answers. Independently
verify outputs before relying on them, including checking sources and reviewing
and testing generated code before execution. Maintain human oversight and do not
use model outputs as the sole basis for decisions with significant consequences.

### Data protection and external content

Hosting on a private server does not by itself guarantee confidentiality or make
all data appropriate to upload. Do not submit passwords, access keys, personal or
sensitive information, or confidential or unpublished material unless its use has
been explicitly authorised under the relevant institutional policies and the
service's data handling arrangements. Submit only data you have permission to use.

External websites, retrieved documents, and tool responses may contain malicious
instructions designed to override your prompt, disclose information, or trigger
unintended actions (prompt injection). Treat this content as untrusted. Review
external access and tool actions, restrict permissions, and never allow model
outputs or external content to execute commands or transmit sensitive data
without your review and authorisation. External services may receive data when
you choose to connect to them.

### Access key and service use

Keep your key secret, do not share it, and report suspected compromise or security
incidents to the facility promptly. Use shared computing resources responsibly.
Access may be restricted or withdrawn in accordance with institutional policies
or operational needs. Availability and suitability for a particular purpose are
not guaranteed. Your first name, last name, and account email address will be
recorded to process your access request.
"""


@dashapp.callback(
    Output('app-content', 'children'),
    Input('session-id', 'data'))
def make_app_content(session_id):
    header, message = check_access('llms')
    if header:
        return dbc.Alert(message, color="danger")
    return dbc.Container([
        html.H2("Request access to facility-hosted LLMs"),
        dbc.Row([
            dbc.Col([
                dbc.Label("First name", html_for="llms-first-name"),
                dbc.Input(id="llms-first-name", type="text", maxLength=128),
            ], md=6),
            dbc.Col([
                dbc.Label("Last name", html_for="llms-last-name"),
                dbc.Input(id="llms-last-name", type="text", maxLength=128),
            ], md=6),
        ], className="mb-3"),
        dbc.Label("Account email", html_for="llms-email"),
        dbc.Input(id="llms-email", value=current_user.email, type="email",
                  disabled=True, className="mb-3"),
        dcc.Markdown(RESPONSIBILITY_NOTICE),
        dbc.Checkbox(
            id="llms-acknowledgement", value=False,
            label="I have read and understood the notice above and acknowledge "
                  "my responsibility for using the service and its outputs.",
            className="mb-3"),
        dbc.Button("Request Key", id="llms-request-key", n_clicks=0,
                   disabled=True, color="primary"),
        html.Div(
            id="llms-request-result", role="status",
            **{"aria-live": "polite", "aria-atomic": "true"},
            style={
                "position": "fixed", "top": "1rem", "left": "50%",
                "transform": "translateX(-50%)", "zIndex": 1080,
                "width": "calc(100% - 2rem)", "maxWidth": "640px",
            },
        ),
    ], className="pt-4", style={"maxWidth": "960px", "paddingBottom": "90px"})


@dashapp.callback(
    Output('llms-request-key', 'disabled'),
    Input('llms-first-name', 'value'),
    Input('llms-last-name', 'value'),
    Input('llms-acknowledgement', 'value'))
def toggle_request_disabled(first_name, last_name, acknowledged):
    return not (
        isinstance(first_name, str) and first_name.strip()
        and isinstance(last_name, str) and last_name.strip()
        and acknowledged is True
    )


@dashapp.callback(
    Output('llms-request-result', 'children'),
    Input('llms-request-key', 'n_clicks'),
    State('llms-first-name', 'value'),
    State('llms-last-name', 'value'),
    State('llms-acknowledgement', 'value'),
    prevent_initial_call=True)
def request_key(n_clicks, first_name, last_name, acknowledged):
    if not n_clicks:
        return dash.no_update
    header, message = check_access('llms')
    if header:
        return dbc.Alert(message, color="danger", dismissable=True)
    if toggle_request_disabled(first_name, last_name, acknowledged):
        return dbc.Alert("Enter your first and last name and acknowledge the "
                         "responsibility notice before requesting a key.", color="warning", dismissable=True)
    first_name, last_name = first_name.strip(), last_name.strip()
    if len(first_name) > 128 or len(last_name) > 128:
        return dbc.Alert("Names must be at most 128 characters each.", color="warning", dismissable=True)
    filename = None
    temporary_filename = None
    try:
        acknowledged_at = datetime.now(ZoneInfo("Europe/Berlin"))
        # Audit every validated, acknowledged click, including duplicate requests.
        # UserLogging timestamps follow the database's naive UTC convention.
        db.session.add(UserLogging(
            email=current_user.email,
            action=f"acknowledged llms request key; APP_VERSION={app.config['APP_VERSION']}",
            date_time=acknowledged_at.astimezone(timezone.utc).replace(tzinfo=None),
        ))
        db.session.commit()
        submission_folder = os.path.dirname(make_submission_file(".llms.xlsx", folder="mpcdf"))
        date = acknowledged_at.strftime("%Y%m%d")
        filename = os.path.join(submission_folder, f"{date}.{current_user.id}.llms.xlsx")
        # Check both legacy and UUID filenames still waiting in the local queue.
        pending_pattern = os.path.join(submission_folder, f"{date}.{current_user.id}.*.llms.xlsx")
        if os.path.exists(filename) or next(iglob(pending_pattern), None) is not None:
            return dbc.Alert("Your request has already been submitted.", color="warning", dismissable=True)
        filename = os.path.join(
            submission_folder, f"{date}.{current_user.id}.{uuid.uuid4().hex}.llms.xlsx")
        # Stage on the same filesystem; consumers only see completed .xlsx files.
        with tempfile.NamedTemporaryFile(
                dir=submission_folder, prefix=".llms-", suffix=".tmp",
                delete=False) as submission_file:
            temporary_filename = submission_file.name
        # Explicit string cells prevent user-provided names becoming Excel formulas.
        with open(temporary_filename, "w+b") as workbook_file, pd.ExcelWriter(
                workbook_file, engine="openpyxl") as writer:
            pd.DataFrame([{
                "first_name": first_name,
                "last_name": last_name,
                "email": current_user.email,
                "acknowledged": True,
                "acknowledged_at": acknowledged_at.isoformat(timespec="seconds"),
                "notice_version": RESPONSIBILITY_NOTICE_VERSION,
            }]).to_excel(writer, sheet_name="LLMs", index=False)
            for column in ("A", "B", "C", "E", "F"):
                writer.sheets["LLMs"][f"{column}2"].data_type = "s"
            pd.DataFrame([{
                "notice_version": RESPONSIBILITY_NOTICE_VERSION,
                "notice_text": RESPONSIBILITY_NOTICE.strip(),
            }]).to_excel(writer, sheet_name="Responsibility notice", index=False)
        # Publish the completed file atomically without overwriting an existing file.
        try:
            os.link(temporary_filename, filename)
        except FileExistsError:
            return dbc.Alert("Your request has already been submitted.", color="warning", dismissable=True)
    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to save LLM access request")
        return dbc.Alert("Your request could not be saved. Please try again or "
                         "contact the facility.", color="danger", dismissable=True)
    finally:
        if temporary_filename is not None:
            try:
                os.unlink(temporary_filename)
            except OSError:
                app.logger.exception("Failed to remove temporary LLM submission")
    return dbc.Alert("Your access request is being processed. You should receive your "
                     "account information by email within the next hour.", color="success", dismissable=True)


@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"))
def toggle_navbar_collapse(n_clicks, is_open):
    return not is_open if n_clicks else is_open
