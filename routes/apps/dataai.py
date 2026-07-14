from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from flask_login import current_user
from flask_caching import Cache
import dash
import io
import os
import re
import uuid
import base64
import pandas as pd
from dash import dcc, html, dash_table, no_update, callback_context
from dash.dependencies import Input, Output, State, MATCH
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from ._dataai import run_dataai, prepare_tables

# Client-side limits (no server cache)
MAX_FILES = 5             # max uploaded files
MAX_UPLOAD_MB = 20        # max total upload size
MAX_TABLE_ROWS = 3000     # rows rendered in a DataTable (full data still downloadable)
MAX_STORE_MB = 40         # base + results kept in dcc.Store; evict oldest results beyond this

# Instruction-box placeholders. Plain before any result; explains referencing once a
# result exists (the label also switches to "Further Instruction" then).
INITIAL_PLACEHOLDER = ("Ask a question about your uploaded data — filter, summarise, sort, "
                       "or combine your tables — and get the answer back as a table.")
FURTHER_PLACEHOLDER = ("Keep going. You can query your uploaded data and any previous "
                       "results — just refer to a table by the name shown in its Source tab, "
                       "such as 'sort result_1 by value' or 'merge result_1 with data_1'.")

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash(
    "dataai",
    url_base_pathname=f'{PAGE_PREFIX}/dataai/',
    meta_tags=META_TAGS,
    server=app,
    external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME],
    title="Data AI",
    assets_folder=app.config["APP_ASSETS"],
    suppress_callback_exceptions=True,
)

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

dashapp.layout = html.Div([
    dcc.Store(data=str(uuid.uuid4()), id='session-id'),
    dcc.Location(id='url', refresh=True),
    html.Div(id="protected-content"),
    html.Div(id="logs-scroll-dummy", style={"display": "none"}),
])


# ── helpers ─────────────────────────────────────────────────────────────────
# Frames are stored in dcc.Store as base64-encoded Parquet so dtypes (dates,
# categoricals, ints/floats) survive the round-trip when results are chained.
def _ser(df):
    return base64.b64encode(df.to_parquet(index=False)).decode("ascii")


def _rj(frame_b64):
    return pd.read_parquet(io.BytesIO(base64.b64decode(frame_b64)))


def _upload_bytes(contents):
    """Approx total decoded size of Dash-uploaded files, from base64 length (no decode)."""
    total = 0
    for c in (contents or []):
        try:
            total += int(len(c.split(",", 1)[1]) * 3 / 4)
        except Exception:
            pass
    return total


def _store_bytes(base, results):
    """Serialized size of everything held in the Store (~what travels the wire)."""
    total = sum(len(v) for v in (base or {}).values())
    for r in (results or []):
        if r.get("data"):
            total += len(r["data"])
    return total


def _enforce_store_cap(base, results):
    """Evict oldest non-tombstoned results (never base, never the latest) until under the
    store cap. Mutates `results` (replacing evicted entries with tombstones). Returns the
    list of evicted names."""
    cap = MAX_STORE_MB * 1024 * 1024
    evicted = []
    while _store_bytes(base, results) > cap:
        idx = next((i for i, r in enumerate(results[:-1]) if r.get("data")), None)
        if idx is None:                       # only base + latest result remain
            break
        ev = results[idx]
        results[idx] = {"name": ev["name"], "shape": ev.get("shape")}  # tombstone (no data)
        evicted.append(ev["name"])
    return evicted


def _table(df, page_size=50):
    shown = df.head(MAX_TABLE_ROWS)           # cap rendered rows; full data stays downloadable
    return dash_table.DataTable(
        data=shown.to_dict("records"),
        columns=[{"name": str(c), "id": str(c)} for c in df.columns],
        fixed_rows={"headers": True},         # sticky header while scrolling
        style_table={"maxHeight": "70vh", "overflowY": "auto", "overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "6px", "fontFamily": "sans-serif"},
        style_header={"backgroundColor": "#5474d8", "color": "white", "fontWeight": "bold"},
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgb(242,242,242)"}
        ],
        page_size=page_size,
        sort_action="native",
        filter_action="native",
    )


def _generate_py(sql, table_names, out_name):
    """A runnable DuckDB script that reproduces a result from the source CSVs."""
    loads = "\n".join(f'con.register("{t}", pd.read_csv("{t}.csv"))' for t in table_names)
    return (
        "import duckdb\n"
        "import pandas as pd\n\n"
        "# Reproduces this Data AI result with DuckDB (the same engine the app uses).\n"
        '# Download each table via its "Data (csv)" button into this folder; the file\n'
        "# names must match the ones below.\n\n"
        "con = duckdb.connect()\n"
        f"{loads}\n\n"
        f'sql = """{sql}"""\n\n'
        "result = con.execute(sql).df()\n"
        "print(result)\n"
        f'result.to_csv("{out_name}.csv", index=False)  # save the output\n'
    )


def _sql_tables(sql, all_names):
    """Table names (from those available) that the SQL references, by word match."""
    names = list(dict.fromkeys(all_names))
    used = [t for t in names if re.search(r"\b" + re.escape(t) + r"\b", sql, re.I)]
    return used or names


def _placeholder_for(label):
    return FURTHER_PLACEHOLDER if label == "Further Instruction" else INITIAL_PLACEHOLDER


def _tombstone(name, shape):
    dims = f" (was {shape[0]} × {shape[1]})" if shape else ""
    return html.Div(
        f"🧹 {name}{dims} was removed to free client-side cache. Re-run to regenerate it.",
        style={"padding": "20px", "color": "#888", "fontStyle": "italic"},
    )


def _dl_buttons(name, is_result=False):
    """Data (csv)/(xlsx) buttons (pattern-matched). For the result frame (is_result), also
    add Query (sql) and Code (py) buttons (fixed ids — one result is shown at a time)."""
    buttons = [
        dbc.Button(html.Span([html.I(className="fas fa-file-csv"), " Data (csv)"]),
                   id={"type": "dl-csv", "index": name}, color="secondary",
                   style={"padding": "6px 12px", "whiteSpace": "nowrap"}),
        dbc.Button(html.Span([html.I(className="fas fa-file-excel"), " Data (xlsx)"]),
                   id={"type": "dl-xlsx", "index": name}, color="secondary",
                   style={"padding": "6px 12px", "whiteSpace": "nowrap"}),
        dcc.Download(id={"type": "dl", "index": name}),
    ]
    if is_result:
        buttons += [
            dbc.Button(html.Span([html.I(className="fas fa-file-code"), " Query (sql)"]),
                       id="dl-sql-btn", color="secondary",
                       style={"padding": "6px 12px", "whiteSpace": "nowrap"}),
            dcc.Download(id="download-sql"),
            dbc.Button(html.Span([html.I(className="fab fa-python"), " Code (py)"]),
                       id="dl-py-btn", color="secondary",
                       style={"padding": "6px 12px", "whiteSpace": "nowrap"}),
            dcc.Download(id="download-py"),
            dbc.Tooltip(
                "Python that reproduces this result with DuckDB. Download each dataframe "
                'with its "Data (csv)" button into the same folder as the script — the '
                "filenames must match (e.g. genes.csv, result_1.csv) — then run it.",
                target="dl-py-btn", placement="top"),
        ]
    return html.Div(buttons, style={"display": "flex", "gap": "8px",
                                    "flexWrap": "wrap", "marginTop": "12px"})


def _df_block(name, df, is_result=False):
    """A titled DataFrame + its download buttons (with a note if rows are truncated)."""
    children = [
        html.Div(
            [
                html.B(name),
                html.Span(f"  ·  {len(df)} rows × {len(df.columns)} cols",
                          style={"color": "#6c757d", "fontSize": "0.85rem"}),
            ],
            style={"marginBottom": "6px"},
        ),
        _table(df),
    ]
    if len(df) > MAX_TABLE_ROWS:
        children.append(html.Div(
            f"Showing first {MAX_TABLE_ROWS:,} of {len(df):,} rows — download for the full table.",
            style={"marginTop": "6px", "fontSize": "0.8em", "color": "#888", "fontStyle": "italic"}))
    children.append(_dl_buttons(name, is_result=is_result))
    if is_result:
        children.append(html.Div(
            "* LLM output can be hallucinated, incomplete, or flawed — please interpret with caution.",
            style={"marginTop": "14px", "fontSize": "0.8em", "color": "#888", "fontStyle": "italic"}))
    return html.Div(children, style={"padding": "20px"})


def _log_block(n, instruction, status_line, sql, prep_errors=None):
    """One markdown entry for the running log: query -> result/error -> SQL."""
    parts = [f"🔎 **Query {n}:** {instruction}"]
    for e in (prep_errors or []):
        parts.append(f"⚠️ {e}")
    parts.append(status_line)
    if sql:
        parts.append("🧩 **Generated SQL:**\n\n```sql\n" + sql + "\n```")
    return "\n\n".join(parts)


def _output_tabs(result_block, source_items, log_blocks, show_disclaimer=False):
    """Result Dataframe / Source Dataframe(s) / Logs (accumulated, newest at bottom).
    source_items: list of {name, df} (live) or {name, df=None, shape} (evicted tombstone)."""
    if source_items:
        source_children = dcc.Tabs([
            dcc.Tab(label=it["name"], children=[
                _df_block(it["name"], it["df"]) if it.get("df") is not None
                else _tombstone(it["name"], it.get("shape"))
            ])
            for it in source_items
        ])
    else:
        source_children = html.Div("No source data.", style={"padding": "20px"})

    if show_disclaimer:
        result_tab_children = [result_block]
    else:
        result_tab_children = [html.Div(result_block, style={"padding": "20px"})]

    log_md = "\n\n---\n\n".join(log_blocks) if log_blocks else "_No queries yet._"

    return dcc.Tabs(
        id="output-tabs", value="tab-result",
        children=[
            dcc.Tab(label="Result Dataframe", value="tab-result", children=result_tab_children),
            dcc.Tab(label="Source Dataframe(s)", value="tab-source", children=[source_children]),
            dcc.Tab(label="Logs", value="tab-logs", children=[
                html.Div(dcc.Markdown(log_md), id="dataai-logs",
                         style={"padding": "20px", "maxHeight": "72vh", "overflowY": "auto"})]),
        ],
    )


def _all_frames(state):
    """name -> frame_b64 for every LIVE frame (base uploads + non-evicted results)."""
    frames = dict(state.get("base") or {})
    for r in state.get("results") or []:
        if r.get("data"):
            frames[r["name"]] = r["data"]
    return frames


# ── layout ──────────────────────────────────────────────────────────────────
@dashapp.callback(
    Output('protected-content', 'children'),
    Input('url', 'pathname')
)
def make_layout(pathname):
    if "dataai" in PRIVATE_ROUTES:
        appdb = PrivateRoutes.query.filter_by(route="dataai").first()
        if not appdb:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        allowed_users = appdb.users or []
        allowed_domains = appdb.users_domains or []
        if not allowed_users and not allowed_domains:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        if (current_user.id not in allowed_users) and (current_user.domain not in allowed_domains):
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    eventlog = UserLogging(email=current_user.email, action="visit dataai")
    db.session.add(eventlog)
    db.session.commit()

    return html.Div(
        [
            make_navbar_logged(
                html.Span(
                    [
                        "Data AI",
                        html.I(className="fas fa-info-circle ms-2", id="dataai-info-icon",
                               style={"cursor": "pointer", "fontSize": "0.7em", "verticalAlign": "super"}),
                    ],
                    style={"display": "inline-flex", "alignItems": "flex-start"}
                ),
                current_user
            ),
            dbc.Tooltip(
                "Data AI uses open models such as Qwen3-Coder or Gemma-4, powered by MPCDF hardware. "
                "It turns your instruction into a read-only SQL query over your data and returns a result "
                "table. LLM output can be wrong — check the generated SQL in the Logs tab.",
                target="dataai-info-icon", placement="right"
            ),

            dcc.Store(id="state-store"),

            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    # File upload (one or more)
                                    html.Div([
                                        html.Div(
                                            dcc.Upload(
                                                id="upload-data",
                                                children=html.Div(
                                                    id="upload-data-text",
                                                    children=["Drag and Drop or ", html.A("Select File(s)")],
                                                    style={"textAlign": "center", "marginTop": 10, "marginBottom": 10}
                                                ),
                                                style={"width": "100%", "borderWidth": "1px", "borderStyle": "dashed",
                                                       "borderRadius": "5px", "marginBottom": "20px",
                                                       "marginTop": "10px", "cursor": "pointer"},
                                                multiple=True,
                                            ),
                                            id="upload-box-wrapper"
                                        ),
                                        dbc.Tooltip(
                                            "Upload one or more files. Supported: Excel, CSV, TSV, TXT, JSON, "
                                            "PDF, Parquet, Feather, MD, HTML, XML.",
                                            target="upload-box-wrapper", placement="bottom"
                                        ),
                                    ], id="file-upload-section"),

                                    # Instruction (label becomes "Further Instruction" once
                                    # results exist, cueing that results are now in scope too).
                                    html.Div([
                                        html.Span([
                                            html.Label("Instruction", id="query-label", style={"margin-top": 15}),
                                            html.I(className="fas fa-info-circle ms-2", id="instr-tooltip-icon",
                                                   style={"cursor": "pointer", "color": "#333333", "fontSize": "0.9em"}),
                                        ], style={"display": "inline-flex", "alignItems": "center"}),
                                        dbc.Tooltip(
                                            "Clear, unambiguous instructions lead to better and faster outputs. "
                                            "Once you have a result you can keep building on it — refer to your "
                                            "uploaded tables and earlier results by the names shown in the Source "
                                            "tabs (such as data_1 or result_1). Each run adds a new result and moves "
                                            "the previous one to Source Dataframe(s).",
                                            target="instr-tooltip-icon", placement="bottom"
                                        ),
                                    ]),
                                    dcc.Textarea(
                                        id="query-input",
                                        placeholder=INITIAL_PLACEHOLDER,
                                        style={"width": "100%", "height": "150px", "padding": "10px"},
                                    ),
                                ],
                                body=True
                            ),
                            html.Div(
                                dbc.Button("Submit", id="run-btn", color="secondary",
                                           className="mt-2", style={"width": "100%"}),
                                id="submit-button-container"
                            ),
                            html.Div(id="btn-state-dummy", style={"display": "none"}),
                            html.Div(id="btn-reset-dummy", style={"display": "none"}),
                        ],
                        xs=12, sm=12, md=6, lg=4, xl=3,
                        align="top",
                        style={"padding": "0px", "margin-bottom": "50px"},
                    ),
                    dbc.Col(
                        [
                            dcc.Loading(
                                id="loading-output-1",
                                type="default",
                                children=[html.Div(id="dataai-output")],
                                style={"margin-top": "50%"},
                            )
                        ],
                        xs=12, sm=12, md=6, lg=8, xl=9,
                        style={"margin-bottom": "50px"},
                    ),
                ],
                align="start", justify="left", className="g-0", style={"width": "100%"},
            ),
            navbar_A,
        ],
        style={"height": "100vh", "verticalAlign": "center"},
    )


@dashapp.callback(
    Output("upload-data-text", "children"),
    Input("upload-data", "filename"),
    State("upload-data", "contents"),
    prevent_initial_call=True,
)
def show_filenames(filenames, contents):
    if not filenames:
        return html.Div(["Drag and Drop or ", html.A("Select File(s)")])
    over_files = len(filenames) > MAX_FILES
    over_size = _upload_bytes(contents) / (1024 * 1024) > MAX_UPLOAD_MB
    names = html.A(", ".join(filenames))
    if over_files or over_size:
        limit = f"max {MAX_FILES} files" if over_files else f"max {MAX_UPLOAD_MB} MB"
        return html.Div([names, html.Div(f"⚠️ Over the limit ({limit})",
                                         style={"fontSize": "0.8em"})],
                        style={"color": "#c0392b"})
    return html.Div([names])


def _sources_view(base, results):
    """Source tabs = uploaded base + every result except the latest. Each item is
    {name, df} (live) or {name, df=None, shape} (evicted tombstone)."""
    items = [{"name": name, "df": _rj(j)} for name, j in base.items()]
    for r in results[:-1]:
        if r.get("data"):
            items.append({"name": r["name"], "df": _rj(r["data"])})
        else:
            items.append({"name": r["name"], "df": None, "shape": r.get("shape")})
    return items


# ── main run ────────────────────────────────────────────────────────────────
# One box. Every query runs over EVERYTHING in scope — the uploaded tables plus all
# previous results (referenced by the names shown in the Source tabs). Each run adds a
# new result_N; the previous result moves to Source Dataframe(s).
@dashapp.callback(
    [Output("dataai-output", "children"),
     Output("state-store", "data"),
     Output("query-input", "value"),
     Output("query-label", "children"),
     Output("query-input", "placeholder")],
    Input("run-btn", "n_clicks"),
    [State("upload-data", "contents"),
     State("upload-data", "filename"),
     State("query-input", "value"),
     State("state-store", "data")],
    prevent_initial_call=True,
)
def run_query(n_clicks, contents, filenames, instruction, state):
    # Guard the whole run so an unexpected error still returns a valid output (which
    # resets the spinner) instead of leaving the Submit button spinning.
    try:
        return _run_query_impl(n_clicks, contents, filenames, instruction, state)
    except Exception as e:
        return (_output_tabs(f"❌ Something went wrong — please try again. ({e})", None,
                             (state or {}).get("log") or []),
                no_update, no_update, no_update, no_update)


def _run_query_impl(n_clicks, contents, filenames, instruction, state):
    instruction = (instruction or "").strip()
    state = state or {}
    sig = list(filenames or [])

    if not contents:
        return (_output_tabs("⚠️ Upload at least one data file.", None, state.get("log") or []),
                state, no_update, no_update, no_update)

    # New upload -> guard size, parse fresh base, reset the chain AND the log.
    new_upload = state.get("sig") != sig or not state.get("base")
    prep_errors = []
    if new_upload:
        reset = {"sig": sig, "base": {}, "results": [], "log": []}
        if len(filenames or []) > MAX_FILES:
            return (_output_tabs(f"⚠️ Too many files ({len(filenames)}). Please upload at "
                                 f"most {MAX_FILES}.", None, []),
                    reset, no_update, "Instruction", INITIAL_PLACEHOLDER)
        up_mb = _upload_bytes(contents) / (1024 * 1024)
        if up_mb > MAX_UPLOAD_MB:
            return (_output_tabs(f"⚠️ Upload too large ({up_mb:.1f} MB). The limit is "
                                 f"{MAX_UPLOAD_MB} MB total.", None, []),
                    reset, no_update, "Instruction", INITIAL_PLACEHOLDER)
        tables, prep_errors = prepare_tables(contents, filenames)
        if not tables:
            return (_output_tabs("❌ Could not read any data from the upload(s).", None,
                                 [f"❌ {e}" for e in prep_errors] or ["❌ No readable data."]),
                    {"sig": sig, "base": {}, "results": [], "log": []}, no_update,
                    "Instruction", INITIAL_PLACEHOLDER)
        base = {name: _ser(df) for name, df in tables.items()}
        state = {"sig": sig, "base": base, "results": [], "log": []}
    base = state["base"]
    results = list(state.get("results") or [])
    log_blocks = list(state.get("log") or [])
    label = "Further Instruction" if results else "Instruction"

    if not instruction:
        return (_output_tabs("⚠️ Enter an instruction.", _sources_view(base, results), log_blocks),
                state, no_update, label, _placeholder_for(label))

    # Query over everything in scope: uploaded tables + all prior results. Unless the
    # instruction names a table, default to the LAST result (or the single uploaded table).
    query_tables = {name: _rj(j) for name, j in _all_frames(state).items()}
    if results:
        default_table = results[-1]["name"]
    elif len(base) == 1:
        default_table = next(iter(base))
    else:
        default_table = None
    result_df, sql, err = run_dataai(query_tables, instruction, default_table=default_table)

    n = len(log_blocks) + 1
    if err:
        log_blocks = log_blocks + [_log_block(n, instruction, f"❌ {err}", sql, prep_errors)]
        state = {**state, "log": log_blocks}
        return (_output_tabs(f"❌ {err}", _sources_view(base, results), log_blocks),
                state, no_update, label, _placeholder_for(label))

    # Success -> add a new result; the previous one becomes a source.
    rname = f"result_{len(results) + 1}"
    rows, cols = len(result_df), len(result_df.columns)
    results = results + [{"name": rname, "data": _ser(result_df), "shape": [rows, cols], "sql": sql}]

    # Keep the Store under its cap: evict oldest results (never base / the latest).
    evicted = _enforce_store_cap(base, results)

    status = f"✅ {rname}: {rows} rows × {cols} cols"
    block = _log_block(n, instruction, status, sql, prep_errors)
    if evicted:
        block += "\n\n🧹 Evicted from cache to stay under " + f"{MAX_STORE_MB} MB: " + ", ".join(evicted)
    log_blocks = log_blocks + [block]
    state = {"sig": sig, "base": base, "results": results, "log": log_blocks}

    return (_output_tabs(_df_block(rname, result_df, is_result=True), _sources_view(base, results),
                         log_blocks, show_disclaimer=True),
            state, "", "Further Instruction", FURTHER_PLACEHOLDER)


# On a new upload, clear the query box and reset the label (a fresh dataset starts clean).
@dashapp.callback(
    [Output("query-input", "value", allow_duplicate=True),
     Output("query-label", "children", allow_duplicate=True),
     Output("query-input", "placeholder", allow_duplicate=True)],
    Input("upload-data", "contents"),
    prevent_initial_call=True,
)
def clear_on_new_upload(contents):
    if contents:
        return "", "Instruction", INITIAL_PLACEHOLDER
    return no_update, no_update, no_update


# ── per-DataFrame downloads (one pattern-matched callback for csv + xlsx) ────
@dashapp.callback(
    Output({"type": "dl", "index": MATCH}, "data"),
    [Input({"type": "dl-csv", "index": MATCH}, "n_clicks"),
     Input({"type": "dl-xlsx", "index": MATCH}, "n_clicks")],
    State("state-store", "data"),
    prevent_initial_call=True,
)
def download_frame(n_csv, n_xlsx, state):
    trig = callback_context.triggered_id      # {"type": "dl-csv"|"dl-xlsx", "index": name}
    if not trig:
        return no_update
    idx = trig["index"]
    frames = _all_frames(state or {})
    if idx not in frames:
        return no_update
    df = _rj(frames[idx])
    if trig["type"] == "dl-xlsx":
        return dcc.send_data_frame(df.to_excel, f"{idx}.xlsx", index=False)
    return dcc.send_data_frame(df.to_csv, f"{idx}.csv", index=False)


# Download the SQL that produced the current result (Result tab only).
@dashapp.callback(
    Output("download-sql", "data"),
    Input("dl-sql-btn", "n_clicks"),
    State("state-store", "data"),
    prevent_initial_call=True,
)
def download_sql(n_clicks, state):
    results = (state or {}).get("results") or []
    if not results or not results[-1].get("sql"):
        return no_update
    last = results[-1]
    return {"content": last["sql"] + "\n", "filename": f"{last['name']}.sql"}


# Download a runnable DuckDB Python script that reproduces the current result.
@dashapp.callback(
    Output("download-py", "data"),
    Input("dl-py-btn", "n_clicks"),
    State("state-store", "data"),
    prevent_initial_call=True,
)
def download_py(n_clicks, state):
    state = state or {}
    results = state.get("results") or []
    if not results or not results[-1].get("sql"):
        return no_update
    last = results[-1]
    all_names = list((state.get("base") or {}).keys()) + [r["name"] for r in results]
    tables = _sql_tables(last["sql"], all_names)
    code = _generate_py(last["sql"], tables, last["name"])
    return {"content": code, "filename": f"{last['name']}.py"}


# ── spinner on the Submit button (rotating messages + safety-net timeout) ────
dashapp.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks || n_clicks < 1) return '';
        var btn = document.getElementById('run-btn');
        if (!btn) return '';
        btn.disabled = true;

        window.dataaiDone = false;
        clearTimeout(window.dataaiTimeout);
        window.dataaiTimeout = setTimeout(function () {
            if (window.dataaiDone) return;
            if (window.dataaiMsgInterval) { clearInterval(window.dataaiMsgInterval); window.dataaiMsgInterval = null; }
            var b = document.getElementById('run-btn');
            if (b) { b.disabled = true; b.innerHTML = "Took too long - consider refresh & retry!"; }
        }, 120000);

        const messages = [
            "Reading your data...",
            "Understanding the question...",
            "Writing the query...",
            "Filtering and joining...",
            "Crunching rows...",
            "Shaping the result...",
            "Still working...",
            "Wrangling the columns...",
            "Double-checking the query...",
            "Assembling the table...",
            "Taking a little longer...",
            "Hang tight..."
        ];
        let i = 0;
        function upd() {
            if (!btn.disabled) return;
            btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status" style="margin-right:6px;"></div> ' + messages[i % messages.length];
            i += 1;
        }
        upd();
        window.dataaiMsgInterval = setInterval(upd, 4000);
        return '';
    }
    """,
    Output("btn-state-dummy", "children"),
    Input("run-btn", "n_clicks"),
)

dashapp.clientside_callback(
    """
    function(children) {
        window.dataaiDone = true;
        clearTimeout(window.dataaiTimeout);
        var btn = document.getElementById('run-btn');
        if (btn) { btn.disabled = false; btn.innerHTML = "Submit"; }
        if (window.dataaiMsgInterval) { clearInterval(window.dataaiMsgInterval); window.dataaiMsgInterval = null; }
        return '';
    }
    """,
    Output("btn-reset-dummy", "children"),
    Input("dataai-output", "children"),
    prevent_initial_call=True,
)

# When the Logs tab is opened, scroll it to the newest entry (bottom). The Logs content
# only mounts in the DOM once its tab is active, so we trigger on the tab selection.
dashapp.clientside_callback(
    """
    function(tab) {
        if (tab !== 'tab-logs') return '';
        setTimeout(function () {
            var el = document.getElementById('dataai-logs');
            if (el) { el.scrollTop = el.scrollHeight; }
        }, 100);
        return '';
    }
    """,
    Output("logs-scroll-dummy", "children"),
    Input("output-tabs", "value"),
    prevent_initial_call=True,
)
