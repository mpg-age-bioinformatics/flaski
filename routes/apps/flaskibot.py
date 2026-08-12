"""Hidden, read-only Flaski AssistBot diagnostic result page."""

from urllib.parse import parse_qs

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask_login import current_user

from myapp import PAGE_PREFIX, app
from myapp.routes._utils import META_TAGS, make_navbar_logged, navbar_A, protect_dashviews
from myapp.routes.apps._utils import ask_for_help

from ._flaskibot import cache_assist_answer, diagnose_error, get_assist_case


FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"
META = META_TAGS + [{"name": "robots", "content": "noindex,nofollow"}]
EXPLANATION_PREVIEW_WORDS = 36
EXPLANATION_PREVIEW_STYLE = {
    "display": "-webkit-box",
    "WebkitBoxOrient": "vertical",
    "WebkitLineClamp": 2,
    "lineHeight": "1.5",
    "maxHeight": "3em",
    "overflow": "hidden",
}

dashapp = dash.Dash(
    "flaskibot",
    url_base_pathname=f"{PAGE_PREFIX}/flaskibot/",
    meta_tags=META,
    server=app,
    external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME],
    title="Flaski AssistBot",
    assets_folder=app.config["APP_ASSETS"],
    suppress_callback_exceptions=True,
)
protect_dashviews(dashapp)

dashapp.layout = html.Div([
    dcc.Location(id="flaskibot-url", refresh=False),
    dcc.Loading(
        html.Div(id="flaskibot-content"),
        type="default",
        color="#000000",
        fullscreen=True,
    ),
])


def _page_shell(content):
    return html.Div([
        make_navbar_logged("Flaski AssistBot", current_user),
        html.Main(
            content,
            style={
                "width": "92%",
                "maxWidth": "1050px",
                "margin": "24px auto 70px auto",
            },
        ),
        navbar_A,
    ])


def _section(title, content, icon=None):
    heading = [
        html.I(className=icon, style={"marginRight": "8px"}) if icon else None,
        title,
    ]
    return dbc.Card([
        dbc.CardHeader(html.H5(heading, style={"margin": 0})),
        dbc.CardBody(content),
    ], className="mb-3", style={"boxShadow": "0 1px 3px rgba(0,0,0,0.08)"})


def _code_block(text):
    """Render untrusted error text literally, never as Markdown or HTML."""
    return html.Pre(
        html.Code(str(text or "")),
        style={
            "backgroundColor": "#f8f9fa",
            "border": "1px solid #dee2e6",
            "borderRadius": "4px",
            "margin": 0,
            "maxHeight": "420px",
            "overflow": "auto",
            "padding": "12px",
            "whiteSpace": "pre-wrap",
            "wordBreak": "break-word",
        },
    )


def _technical_explanation(text):
    explanation = str(text or "")
    words = explanation.split()
    if len(words) <= EXPLANATION_PREVIEW_WORDS:
        return dcc.Markdown(explanation)

    preview = " ".join(words[:EXPLANATION_PREVIEW_WORDS]) + "…"
    return [
        html.Div(
            dcc.Markdown(preview),
            id="flaskibot-explanation-preview",
            style=EXPLANATION_PREVIEW_STYLE,
        ),
        dbc.Collapse(
            dcc.Markdown(explanation),
            id="flaskibot-explanation-collapse",
            is_open=False,
        ),
        dbc.Button(
            "Show more",
            id="flaskibot-explanation-toggle",
            color="link",
            size="sm",
            className="p-0 mt-2",
            n_clicks=0,
        ),
    ]


def _invalid_case_page():
    return _page_shell([
        dbc.Alert(
            [
                html.H4("This diagnostic link is unavailable", className="alert-heading"),
                html.P(
                    "The AssistBot case may have expired, belonged to another session, "
                    "or could not be created. Return to the original Flaski tab and use "
                    "the error toast or Ice Cream support."
                ),
            ],
            color="warning",
        )
    ])


def _report_page(token, case, report):
    return _page_shell([
        dcc.Store(id="flaskibot-case-token", data=token),
        html.Div([
            html.H2("Flaski AssistBot", style={"marginBottom": "6px"}),
            html.Div(
                "* This best-effort AI explanation is grounded in Flaski code and infrastructure; "
                "LLM output can be hallucinated, incomplete, or flawed — please interpret "
                "with caution.",
                style={"fontSize": "0.8em", "color": "#888", "fontStyle": "italic"},
            ),
        ], className="mb-4"),
        _section(
            "Likely cause",
            [
                dcc.Markdown(report.get("likely_cause", "")),
                html.Small(
                    f"Confidence: {report.get('confidence', 'Unavailable')}",
                    style={"color": "#6c757d"},
                ),
            ],
            "fas fa-search",
        ),
        _section(
            "What you can try",
            dcc.Markdown(report.get("solution", "")),
            "fas fa-tools",
        ),
        _section(
            "Short error",
            _code_block(case.get("short_error", "")),
            "fas fa-exclamation-circle",
        ),
        _section(
            "Technical error",
            html.Details([
                html.Summary("Show sanitized traceback", style={"cursor": "pointer", "fontWeight": 600}),
                html.Div(_code_block(case.get("long_error", "")), className="mt-3"),
            ]),
            "fas fa-code",
        ),
        _section(
            "Technical explanation",
            _technical_explanation(report.get("explanation", "")),
            "fas fa-info-circle",
        ),
        dbc.Card([
            dbc.CardBody([
                html.H5("Still need help?"),
                html.P(
                    "Press Ice Cream to send an explicit help request with this sanitized "
                    "error to the Flaski team."
                ),
                dbc.Button(
                    "Ice Cream",
                    id="flaskibot-ice-cream",
                    color="dark",
                    outline=True,
                    n_clicks=0,
                ),
                html.Div(id="flaskibot-support-feedback", className="mt-3"),
            ])
        ], className="mb-3"),
    ])


@dashapp.callback(
    Output("flaskibot-content", "children"),
    Input("flaskibot-url", "search"),
)
def render_diagnostic(search):
    token = (parse_qs((search or "").lstrip("?")).get("case") or [""])[0]
    case = get_assist_case(token)
    if not case:
        return _invalid_case_page()

    report = case.get("answer")
    if not isinstance(report, dict):
        report = diagnose_error(case)
        cache_assist_answer(token, report)
    return _report_page(token, case, report)


@dashapp.callback(
    Output("flaskibot-explanation-collapse", "is_open"),
    Output("flaskibot-explanation-preview", "style"),
    Output("flaskibot-explanation-toggle", "children"),
    Input("flaskibot-explanation-toggle", "n_clicks"),
    State("flaskibot-explanation-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_explanation(n_clicks, is_open):
    if not n_clicks:
        raise PreventUpdate
    show_full_explanation = not is_open
    preview_style = {"display": "none"} if show_full_explanation else EXPLANATION_PREVIEW_STYLE
    button_label = "Show less" if show_full_explanation else "Show more"
    return show_full_explanation, preview_style, button_label


@dashapp.callback(
    Output("flaskibot-support-feedback", "children"),
    Output("flaskibot-ice-cream", "disabled"),
    Input("flaskibot-ice-cream", "n_clicks"),
    State("flaskibot-case-token", "data"),
    prevent_initial_call=True,
)
def request_support(n_clicks, token):
    if not n_clicks:
        raise PreventUpdate
    case = get_assist_case(token)
    if not case:
        return (
            dbc.Alert("This diagnostic case has expired. Please use the original Flaski tab.", color="warning"),
            True,
        )
    try:
        ask_for_help(
            case.get("long_error") or case.get("short_error") or "Flaski AssistBot error unavailable",
            current_user,
            case.get("app") or "flaskibot",
            session_data=None,
        )
        return (
            dbc.Alert(
                "Your help request was sent to the Flaski team.", color="success", dismissable=True
            ),
            True,
        )
    except Exception:
        return (
            dbc.Alert(
                "The help request could not be sent. Please return to the original tab and try Ice Cream there.",
                color="danger",
                dismissable=True,
            ),
            False,
        )


@dashapp.callback(
    Output("navbar-collapse", "is_open"),
    Input("navbar-toggler", "n_clicks"),
    State("navbar-collapse", "is_open"),
    prevent_initial_call=True,
)
def toggle_navbar(n_clicks, is_open):
    return (not is_open) if n_clicks else is_open
