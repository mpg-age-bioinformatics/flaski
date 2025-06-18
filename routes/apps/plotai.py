from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from flask_login import current_user
from flask_caching import Cache
from werkzeug.utils import secure_filename
import plotly.graph_objects as go
import dash
import os
import uuid
import io
import json
from dash import dcc, html, callback_context, no_update
from dash.dependencies import Input, Output, State
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
from myapp.routes.apps._utils import make_table, make_except_toast
import dash_bootstrap_components as dbc
import pandas as pd
from ._plotai import plotai_main_interface, plotai_generate_code

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"
dashapp = dash.Dash("plotai", url_base_pathname=f'{PAGE_PREFIX}/plotai/', meta_tags=META_TAGS, server=app, external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME], title="Plot AI", assets_folder=app.config["APP_ASSETS"])

protect_dashviews(dashapp)

if app.config["SESSION_TYPE"] == "sqlalchemy":
    import sqlalchemy
    engine = sqlalchemy.create_engine(app.config["SQLALCHEMY_DATABASE_URI"], echo=True)
    app.config["SESSION_SQLALCHEMY"] = engine
elif app.config["CACHE_TYPE"] == "RedisCache":
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisCache',
        'CACHE_REDIS_URL': 'redis://:%s@%s' % (os.environ.get('REDIS_PASSWORD'), app.config['REDIS_ADDRESS']),
    })
elif app.config["CACHE_TYPE"] == "RedisSentinelCache":
    cache = Cache(dashapp.server, config={
        'CACHE_TYPE': 'RedisSentinelCache',
        'CACHE_REDIS_SENTINELS': [
            [os.environ.get('CACHE_REDIS_SENTINELS_address'), int(os.environ.get('CACHE_REDIS_SENTINELS_port'))]
        ],
        'CACHE_REDIS_SENTINEL_MASTER': os.environ.get('CACHE_REDIS_SENTINEL_MASTER')
    })



# ------------------------------------------------------------------------------
# Helper Methods
# ------------------------------------------------------------------------------

def plotai_generate_modal(modal_type, label="Filename"):
    if modal_type in ["pdf", "png"]:
        modal_footer = dbc.ModalFooter([
            dbc.Button("Download View", id=f"{modal_type}-filename-download", className="ms-auto", n_clicks=0),
            dbc.Button("Download Full", id=f"{modal_type}-full-download", n_clicks=0),
        ])
    else:
        modal_footer = dbc.ModalFooter(dbc.Button("Download", id=f"{modal_type}-filename-download", className="ms-auto", n_clicks=0))

    return dbc.Modal(
        [
            dbc.ModalHeader(label),
            dbc.ModalBody([dcc.Input(id=f"{modal_type}-filename", value=f"plotai.{modal_type}", type="text", style={"width":"100%"})]),
            modal_footer
        ],
        id=f"{modal_type}-filename-modal",
        is_open=False,
    )


def plotai_generate_button(filetype, label, icon_class):
    if filetype in ["pdf", "png"]:
        download_sec = html.Div([
            dcc.Download(id=f"download-{filetype}"),
            dcc.Download(id=f"download-full-{filetype}")
        ])
    else:
        download_sec = dcc.Download(id=f"download-{filetype}")

    
    return html.Div([
        dbc.Button(
            html.Span([html.I(className=icon_class), f" {label}"]),
            id=f"download-{filetype}-btn",
            color="secondary",
            style={"padding": "6px 12px", "whiteSpace": "nowrap"}
        ),
        download_sec
    ])


def plotai_eventlog(action_text):
    try:
        eventlog = UserLogging(email=current_user.email,action=action_text)
        db.session.add(eventlog)
        db.session.commit()
    except Exception:
        pass

# ------------------------------------------------------------------------------
# Generate Base Layout
# ------------------------------------------------------------------------------

dashapp.layout = html.Div([
    dcc.Store(data=str(uuid.uuid4()), id='session-id'),
    dcc.Location(id='url', refresh=True),
    html.Div(id="protected-content")
])

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname')
)
def make_layout(pathname):
    # Visit eventlog
    plotai_eventlog("visit plotai")

    # HTML content from here
    protected_content=html.Div(
        [
            # Navbar with tooltip
            make_navbar_logged(
                html.Span(
                    [
                        "Plot AI",
                        html.I(
                            className="fas fa-info-circle ms-2",
                            id="plotai-info-icon",
                            style={
                                "cursor": "pointer", "fontSize": "0.7em", "verticalAlign": "super"
                            }
                        )
                    ],
                    style={"display": "inline-flex", "alignItems": "flex-start"}
                ),
                current_user
            ),
            dbc.Tooltip(
                "Plot AI uses models such as Qwen2.5 and LLaMA-3, powered by GWDG hardware. Be aware that LLM models can produce hallucinated content. It may fail to generate output, or the resulting plot can be flawed — interpret with caution.",
                target="plotai-info-icon",
                placement="right"
            ),

            html.Div(id="app_access"),
            # html.Div(id="redirect-app"),
            dcc.Store(data=str(uuid.uuid4()), id='session-id'),
            dcc.Store(id="plot-generated", data=False),

            dbc.Row(
                [
                    dbc.Col( 
                        [
                            dbc.Card(
                                [
                                    # File Upload
                                    html.Div([
                                        html.Div(
                                            dcc.Upload(
                                                id='upload-data',
                                                children=html.Div(
                                                    id='upload-data-text',
                                                    children=['Drag and Drop or ', html.A('Select File')],
                                                    style={'textAlign': 'center', 'marginTop': 10, 'marginBottom': 10}
                                                ),
                                                style={'width': '100%', 'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px', 'marginBottom': '20px', 'marginTop': '10px', 'cursor': 'pointer'},
                                                multiple=False
                                            ),
                                            id='upload-box-wrapper'
                                        ),
                                        dbc.Tooltip(
                                            "Preferred formats: Excel, CSV, TSV, JSON, HTML, XML, TXT — but Plot AI will give any readable file a shot!",
                                            target='upload-box-wrapper',
                                            placement='bottom'
                                        )
                                    ]),

                                    # Text Content textarea
                                    html.Div([
                                        html.Span([
                                            html.Label("(OR) Text Content", style={"margin-top": 15}),
                                            html.I(className="fas fa-info-circle ms-2", id="textcontent-tooltip-icon", style={"cursor": "pointer", "color": "#333333", "fontSize": "0.9em"})
                                        ], style={"display": "inline-flex", "alignItems": "center"}),

                                        dbc.Tooltip(
                                            "From your structured/unstructured text, Plot AI will attempt to construct a meaningful dataset.",
                                            target="textcontent-tooltip-icon",
                                            placement="bottom"
                                        )
                                    ]),
                                    dcc.Textarea(
                                        id='text-content',
                                        placeholder="No file? - Paste your text content here.",
                                        style={'width': '100%', 'height': '150px', 'padding': '10px', 'marginBottom': '10px'}
                                    ),

                                    # Instructions textarea
                                    html.Div([
                                        html.Span([
                                            html.Label("Instructions (optional)", style={"margin-top": 15}),
                                            html.I(className="fas fa-info-circle ms-2", id="instructions-tooltip-icon", style={"cursor": "pointer", "color": "#333333", "fontSize": "0.9em"})
                                        ], style={"display": "inline-flex", "alignItems": "center"}),

                                        dbc.Tooltip(
                                            "Ambiguous or conflicting instructions can lead to failure or longer generation times.",
                                            target="instructions-tooltip-icon",
                                            placement="bottom"
                                        )
                                    ]),
                                    dcc.Textarea(
                                        id='additional-instructions',
                                        placeholder="Skip to let Plot AI decide - or include any plotting preferences here. Be clear and complete as it does not retain chat history.",
                                        style={'width': '100%', 'height': '150px', 'padding': '10px'}
                                    ),
                                ],
                                body=True
                            ),
                            html.Div(
                                dbc.Button(
                                    "Submit",
                                    id="submit-button-state",
                                    color="secondary",
                                    className="mt-2",
                                    style={"width": "100%"}
                                ),
                                id="submit-button-container"
                            ),
                            html.Div(id="btn-state-dummy", style={"display": "none"}),
                            html.Div(id="reset-btn-dummy", style={"display": "none"}),

                        ],
                        xs=12,sm=12,md=6,lg=4,xl=3,
                        align="top",
                        style={"padding":"0px","margin-bottom":"50px"} 
                    ),               
                    dbc.Col(
                        [
                          dcc.Loading(
                              id="loading-output-1",
                              type="default",
                              children=[ html.Div(id="plotai-output")],
                              style={"margin-top":"50%"} 
                          )
                        ],
                        xs=12,sm=12,md=6,lg=8,xl=9,
                        style={"margin-bottom":"50px"}
                    )
                ],
                align="start",
                justify="left",
                className="g-0",
                style={"width":"100%"}
            ),

            plotai_generate_modal("pdf"),
            plotai_generate_modal("png"),
            plotai_generate_modal("xlsx"),
            plotai_generate_modal("csv"),
            plotai_generate_modal("json"),
            plotai_generate_modal("py"),

            navbar_A,
        ],
        style={"height":"100vh","verticalAlign":"center"}
    )
    return protected_content


# ------------------------------------------------------------------------------
# Generate Figure, Data and Logs Output
# ------------------------------------------------------------------------------

@dashapp.callback(
    Output("plotai-output", "children"),
    Output("plot-generated", "data"),
    Input("submit-button-state", "n_clicks"),
    State("upload-data", "contents"),
    State("upload-data", "filename"),
    State("text-content", "value"),
    State("additional-instructions", "value"),
    prevent_initial_call=True
)
def update_plotai_output(n_clicks, contents, filename, text_content, instructions):
    triggered_input = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered_input != 'submit-button-state':
        return no_update

    if not (contents or text_content):
        return html.Div([dcc.Markdown("❌ Please provide a file or text content to generate a plot.", style={"padding": "20px"})]), False

    try:
        fig, spec, df, logs = plotai_main_interface(
            input_contents=contents,
            filename=filename,
            text_content=text_content,
            additional_instructions=instructions
        )

        if not fig:
            e_text = Exception("\n".join(logs) or "Unknown issue during plot generation.")
            _ = make_except_toast("There was a problem generating your plot:", "plotai-soft-failure", e_text, current_user, "plotai")
    
    except Exception as e:
        _ = make_except_toast("There was a problem generating your plot:", "plotai-hard-failure", e, current_user, "plotai")
        return html.Pre(f"❌ There was a problem generating your plot: {e}", style={"padding": "40px"}), False

    tabs = []

    # Tab 1: Figure
    tabs.append(
        dcc.Tab(
            label="Figure",
            children=[
                dcc.Loading(
                    type="default",
                    style={"padding": "20px"},
                    children=[
                        html.Div(
                            [
                                dcc.Graph(figure=fig, id="graph", config={'modeBarButtonsToRemove':["toImage"], 'displaylogo': False}),
                                dcc.Store(id="plotai-spec", data=spec),
                                html.Div(
                                    [
                                        plotai_generate_button("pdf", "PDF", "fas fa-file-pdf"),
                                        plotai_generate_button("png", "PNG", "fas fa-image"),
                                        plotai_generate_button("xlsx", "Data (xlsx)", "fas fa-file-excel"),
                                        plotai_generate_button("csv", "Data (csv)", "fas fa-file-csv"),
                                        plotai_generate_button("json", "Plotly Spec (json)", "fas fa-file-code"),
                                        plotai_generate_button("py", "Code (py)", "fab fa-python"),
                                    ],
                                    id="download-buttons-div",
                                    # style={"marginTop": "20px"}
                                    style={"display": "flex", "gap": "8px", "flexWrap": "wrap", "paddingLeft": "40px", "marginTop": "15px"}
                                )
                            ]
                        ) if fig else html.Div("❌ Failed to generate plot.", style={"padding": "40px"})
                    ]
                )
            ]
        )
    )

    # Tab 2: DataFrame
    if df is not None:
        # table = dbc.Table.from_dataframe(df.head(100), striped=True, bordered=True, hover=True)
        table = make_table(df, "plotai-df-table")
    else:
        table = html.Div("❌ No DataFrame to display.", style={"padding": "20px"})

    tabs.append(
        dcc.Tab(
            label="DataFrame",
            children=[
                html.Div(table, style={"padding": "20px", "overflowX": "auto"})
            ]
        )
    )

    # Tab 3: Logs
    tabs.append(
        dcc.Tab(
            label="Logs",
            children=[
                html.Pre("\n".join(logs), style={"padding": "20px", "whiteSpace": "pre-wrap"})
            ]
        )
    )

    return dcc.Tabs(tabs), bool(fig)


@dashapp.callback(
    Output('upload-data-text', 'children'),
    Input('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_upload_filename(filename):
    if filename:
        return html.Div([
            html.A(filename)
        ])
    return html.Div(['Drag and Drop or ', html.A('Select File')])


# ------------------------------------------------------------------------------
# Modal Toggle Callbacks
# ------------------------------------------------------------------------------

@dashapp.callback(
    Output("pdf-filename-modal", "is_open"),
    [Input("download-pdf-btn", "n_clicks"), Input("pdf-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("pdf-filename-modal", "is_open"),
    prevent_initial_call=True
)
def handle_pdf_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-pdf-btn" and n1) or (t == "pdf-filename-download" and n2) else False if t == "plot-generated" else is_open


@dashapp.callback(
    Output("png-filename-modal", "is_open"),
    [Input("download-png-btn", "n_clicks"), Input("png-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("png-filename-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_png_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-png-btn" and n1) or (t == "png-filename-download" and n2) else False if t == "plot-generated" else is_open


@dashapp.callback(
    Output("xlsx-filename-modal", "is_open"),
    [Input("download-xlsx-btn", "n_clicks"), Input("xlsx-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("xlsx-filename-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_xlsx_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-xlsx-btn" and n1) or (t == "xlsx-filename-download" and n2) else False if t == "plot-generated" else is_open


@dashapp.callback(
    Output("csv-filename-modal", "is_open"),
    [Input("download-csv-btn", "n_clicks"), Input("csv-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("csv-filename-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_csv_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-csv-btn" and n1) or (t == "csv-filename-download" and n2) else False if t == "plot-generated" else is_open


@dashapp.callback(
    Output("json-filename-modal", "is_open"),
    [Input("download-json-btn", "n_clicks"), Input("json-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("json-filename-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_json_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-json-btn" and n1) or (t == "json-filename-download" and n2) else False if t == "plot-generated" else is_open


@dashapp.callback(
    Output("py-filename-modal", "is_open"),
    [Input("download-py-btn", "n_clicks"), Input("py-filename-download", "n_clicks"), Input("plot-generated", "data")],
    State("py-filename-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_py_modal(n1, n2, plot_generated, is_open):
    t = callback_context.triggered[0]["prop_id"].split(".")[0]
    return not is_open if (t == "download-py-btn" and n1) or (t == "py-filename-download" and n2) else False if t == "plot-generated" else is_open


# ------------------------------------------------------------------------------
# Download Callbacks
# ------------------------------------------------------------------------------

@dashapp.callback(
    Output("download-pdf", "data"),
    Input("pdf-filename-download", "n_clicks"),
    State("graph", "figure"),
    State("pdf-filename", "value"),
    prevent_initial_call=True
)
def export_pdf(n_clicks, fig_dict, filename):
    if not fig_dict: return no_update
    plotai_eventlog("download figure plotai")
    fig = go.Figure(fig_dict)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".pdf") else f"{filename}.pdf"
    return dcc.send_bytes(lambda f: fig.write_image(f, format="pdf"), filename)


@dashapp.callback(
    Output("download-full-pdf", "data"),
    Input("pdf-full-download", "n_clicks"),
    State("plotai-spec", "data"),
    State("pdf-filename", "value"),
    prevent_initial_call=True
)
def export_full_pdf(n_clicks, fig_dict, filename):
    if not fig_dict: return no_update
    plotai_eventlog("download figure plotai")
    fig = go.Figure(**fig_dict)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".pdf") else f"{filename}.pdf"
    fig.update_layout(autosize=False, width=2000, height=1200, margin=dict(l=150, r=150, t=150, b=180))
    return dcc.send_bytes(lambda f: fig.write_image(f, format="pdf"), filename)


@dashapp.callback(
    Output("download-png", "data"),
    Input("png-filename-download", "n_clicks"),
    State("graph", "figure"),
    State("png-filename", "value"),
    prevent_initial_call=True
)
def export_png(n_clicks, fig_dict, filename):
    if not fig_dict: return no_update
    plotai_eventlog("download figure plotai")
    fig = go.Figure(fig_dict)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".png") else f"{filename}.png"
    return dcc.send_bytes(lambda f: fig.write_image(f, format="png"), filename)


@dashapp.callback(
    Output("download-full-png", "data"),
    Input("png-full-download", "n_clicks"),
    State("plotai-spec", "data"),
    State("png-filename", "value"),
    prevent_initial_call=True
)
def export_full_png(n_clicks, fig_dict, filename):
    if not fig_dict: return no_update
    plotai_eventlog("download figure plotai")
    fig = go.Figure(**fig_dict)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".png") else f"{filename}.png"
    fig.update_layout(autosize=False, width=2000, height=1200, margin=dict(l=150, r=150, t=150, b=180))
    return dcc.send_bytes(lambda f: fig.write_image(f, format="png"), filename)


@dashapp.callback(
    Output("download-xlsx", "data"),
    Input("xlsx-filename-download", "n_clicks"),
    State("plotai-df-table", "data"),
    State("xlsx-filename", "value"),
    prevent_initial_call=True
)
def download_xlsx(n_clicks, table_data, filename):
    if not table_data: return no_update
    plotai_eventlog("download data plotai")
    df = pd.DataFrame(table_data)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".xlsx") else f"{filename}.xlsx"
    return dcc.send_bytes(lambda f: df.to_excel(f, index=False), filename)


@dashapp.callback(
    Output("download-csv", "data"),
    Input("csv-filename-download", "n_clicks"),
    State("plotai-df-table", "data"),
    State("csv-filename", "value"),
    prevent_initial_call=True
)
def download_csv(n_clicks, table_data, filename):
    if not table_data: return no_update
    plotai_eventlog("download data plotai")
    df = pd.DataFrame(table_data)
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".csv") else f"{filename}.csv"
    return dcc.send_bytes(lambda f: df.to_csv(f, index=False), filename)


@dashapp.callback(
    Output("download-json", "data"),
    Input("json-filename-download", "n_clicks"),
    State("plotai-spec", "data"),
    State("json-filename", "value"),
    prevent_initial_call=True
)
def download_json(n_clicks, spec, filename):
    if not spec: return no_update
    plotai_eventlog("download code plotai")
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".json") else f"{filename}.json"
    json_string = json.dumps(spec, indent=2)
    return dcc.send_bytes(lambda f: f.write(json_string.encode("utf-8")), filename)


@dashapp.callback(
    Output("download-py", "data"),
    Input("py-filename-download", "n_clicks"),
    State("plotai-spec", "data"),
    State("py-filename", "value"),
    prevent_initial_call=True
)
def download_py(n_clicks, spec, filename):
    if not spec: return no_update
    plotai_eventlog("download code plotai")
    filename = secure_filename(filename or "plotai")
    filename = filename if filename.lower().endswith(".py") else f"{filename}.py"
    py_code = plotai_generate_code(spec, filename)
    return dcc.send_bytes(lambda f: f.write(py_code.encode("utf-8")), filename)


# ------------------------------------------------------------------------------
# Client side callback to disable submit button and show info
# ------------------------------------------------------------------------------

dashapp.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks || n_clicks < 1) return '';

        var btn = document.getElementById('submit-button-state');
        if (!btn) return '';

        btn.disabled = true;

        const messages = [
            "Nice! Data in, ideas forming...",
            "Let the plotting commence!",
            "It may take a bit...",
            "Trust the process!",
            "Finding meaning in this madness...",
            "Drawing invisible lines... for now",
            "Negotiating with data points...",
            "Slow and steady makes nice plots",
            "Exploring possibilities...",
            "Looking for a direction, literally",
            "Still going..",
            "This must be a really deep plot",
            "Thinking really hard. Possibly too hard",
            "Longer than usual, still trying...",
            "Plot AI is Frozen in awe of your dataset",
            "Thinking really hard. Possibly too hard.",
            "Still threading... this fabric is tough",
            "Maybe go stretch your legs?",
            "Things got quiet... too quiet",
            "Either brilliance is happening...",
            "Or this is very stuck.",
            "If this fails...",
            "Just know Plot AI gave it everything",
            "Sending a rescue party",
            "Into the data void...",
            "We have officially entered the",
            "\'THIS MIGHT CRASH\' zone.",
            "Might have asked too much of the models",
            "Plot AI was last seen inside a loop",
            "Or have quietly left the room",
            "This feels... suspiciously frozen.",
            "Still high hope? ...",
            "You haveve been incredibly patient",
            "Possibly too patient",
            "This is not just a graph anymore",
            "It is a test of character",
            "Know that we are doing our best. Kind of.",
            "We are running out of messages... and hope",
            "Message tank: empty. Plot: still pending.",
            "Spinner is getting dizzy",
            "We must go back to the",
            "Circle of life...",
            "May the force be with you"
        ];

        let index = 0;

        function updateMessage() {
            if (!btn.disabled) return;  // stop updating if button is re-enabled
            btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status" style="margin-right:6px;"></div> ' + messages[index % messages.length];
            index += 1;
        }

        updateMessage();  // set immediately
        window.plotaiMessageInterval = setInterval(updateMessage, 5000);  // every 15s

        return '';
    }
    """,
    Output("btn-state-dummy", "children"),
    Input("submit-button-state", "n_clicks")
)

dashapp.clientside_callback(
    """
    function(children) {
        var btn = document.getElementById('submit-button-state');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = "Submit";
        }
        if (window.plotaiMessageInterval) {
            clearInterval(window.plotaiMessageInterval);
            window.plotaiMessageInterval = null;
        }
        return '';
    }
    """,
    Output("reset-btn-dummy", "children"),
    Input("plotai-output", "children"),
    prevent_initial_call=True
)