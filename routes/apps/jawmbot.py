from myapp import app, PAGE_PREFIX, PRIVATE_ROUTES
from myapp import db
from myapp.models import UserLogging, PrivateRoutes
from flask_login import current_user
from flask_caching import Cache
import dash
import os
import uuid
from dash import dcc, html, callback_context, no_update
from dash.dependencies import Input, Output, State
from myapp.routes._utils import META_TAGS, navbar_A, protect_dashviews, make_navbar_logged
import dash_bootstrap_components as dbc
from ._jawmbot import chat_jawm

FONT_AWESOME = "https://use.fontawesome.com/releases/v5.7.2/css/all.css"

dashapp = dash.Dash(
    "jawmbot",
    url_base_pathname=f'{PAGE_PREFIX}/jawmbot/',
    meta_tags=META_TAGS,
    server=app,
    external_stylesheets=[dbc.themes.BOOTSTRAP, FONT_AWESOME],
    title="jawm AssistBot",
    assets_folder=app.config["APP_ASSETS"]
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

dashapp.layout = html.Div(
    [
        dcc.Store(data=str(uuid.uuid4()), id='session-id'),
        dcc.Location(id='url', refresh=False),
        html.Div(id="protected-content"),
        # Dummy divs for clientside callbacks
        html.Div(id="dummy-scroll", style={"display": "none"}),
        html.Div(id="btn-state-dummy", style={"display": "none"})
    ]
)

@dashapp.callback(
    Output('protected-content', 'children'),
    Input('session-id', 'data')
)
def make_layout(session_id):
    if "jawmbot" in PRIVATE_ROUTES :
        appdb=PrivateRoutes.query.filter_by(route="jawmbot").first()
        if not appdb:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        allowed_users=appdb.users or []
        allowed_domains=appdb.users_domains or []
        if not allowed_users and not allowed_domains:
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")
        if ( current_user.id not in allowed_users ) and ( current_user.domain not in allowed_domains ):
            return dcc.Location(pathname=f"{PAGE_PREFIX}/", id="index")

    ## check if user is authorized
    eventlog = UserLogging(email=current_user.email, action="visit jawmbot")
    db.session.add(eventlog)
    db.session.commit()

    protected_content = html.Div(
        [
            make_navbar_logged(
                html.Span(
                    [
                        "jawm AssistBot",
                        html.I(
                            className="fas fa-info-circle ms-2",
                            id="jawmbot-info-icon",
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
                "This assistant answers questions about jawm workflow manager from its documentation and source code, using open models on MPCDF hardware. LLM answers can be incomplete or wrong — interpret with caution.",
                target="jawmbot-info-icon",
                placement="bottom"
            ),
            html.Div(style={"marginTop": "10px"}),  # Added space between navbar and chat container
            html.Div(
                [
                    dcc.Store(id="chat-history", data=[]),
                    dcc.Store(id="conversation-history", data=[]),
                    html.Div(
                        id="chat-container",
                        style={
                            "height": "calc(100vh - 200px)",
                            "overflowY": "auto",
                            "padding": "10px",
                            "paddingBottom": "100px",
                            "display": "flex",
                            "flexDirection": "column"
                        }
                    ),
                    html.Div(
                        [
                            dbc.Textarea(
                                id="user-input",
                                placeholder="Ask about jawm — running modules, configuration, debugging, CLI...",
                                style={"width": "100%", "resize": "none", "minHeight": "100px", "border": "3px solid #ddd"}
                            ),
                            # Wrap the ASK button in a container so we can update it
                            html.Div(
                                dbc.Button(
                                    "ASK",
                                    id="send-btn",
                                    color="secondary",
                                    className="mt-2",
                                    style={"width": "100%"}
                                ),
                                id="send-btn-container"
                            )
                        ],
                        style={
                            "width": "90%",
                            "maxWidth": "1200px",
                            "position": "fixed",
                            "bottom": "50px",
                            "left": "50%",
                            "transform": "translateX(-50%)",
                            "zIndex": "10000",
                        },
                    ),
                ],
                style={
                    "width": "90%",
                    "maxWidth": "1200px",
                    "margin": "auto",
                    "padding": "20px",
                    "border": "1px solid #ddd",
                    "borderRadius": "10px",
                    "backgroundColor": "#f8f9fa",
                },
            ),
            navbar_A,
        ]
    )
    return protected_content

@dashapp.callback(
    [Output("chat-container", "children"),
     Output("user-input", "value"),
     Output("conversation-history", "data")],  # Store conversation history
    [Input("send-btn", "n_clicks")],
    [State("user-input", "value"),
     State("chat-container", "children"),
     State("conversation-history", "data")],  # Retrieve stored history
    prevent_initial_call=True
)
def update_chat(n_clicks, user_message, chat_history, conversation_history):
    if not chat_history:
        chat_history = []

    if conversation_history is None:
        conversation_history = []

    # Get bot response and updated conversation history
    bot_response_text, conversation_history = chat_jawm(user_message, conversation_history)

    # Wrap the bot response in a Loading component so it shows a spinner
    bot_response = dcc.Loading(
        type="default",
        children=[dcc.Markdown(bot_response_text, mathjax=True)]
    )

    # Append messages to UI chat history
    user_div = html.Div(
        [html.B("🤓    "), html.B(user_message)],
        className="last-message",
        style={"marginTop": "20px", "marginBottom": "20px", "textAlign": "right"}
    )
    bot_div = html.Div(
        [html.B("🛠️    "), bot_response],
        style={"marginTop": "20px", "marginBottom": "20px", "textAlign": "left"}
    )

    chat_history.extend([user_div, bot_div])

    return chat_history, "", conversation_history  # Return updated history


# Clientside callback: after chat updates, scroll to the last message, re-enable the
# ASK button, and add Copy/Download buttons to each code block.
dashapp.clientside_callback(
    """
    function(children) {
        setTimeout(function(){
            var messages = document.getElementsByClassName('last-message');
            if (messages.length > 0) {
                messages[messages.length - 1].scrollIntoView({behavior: 'smooth'});
            }
            // Re-enable the button and reset its content
            var btn = document.getElementById('send-btn');
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = "ASK";
            }
            // Decorate each code block with Copy + Download buttons (once each)
            var blocks = document.querySelectorAll('#chat-container pre');
            blocks.forEach(function(pre) {
                if (pre.dataset.decorated) { return; }
                pre.dataset.decorated = "1";
                var code = pre.querySelector('code');
                var text = code ? code.innerText : pre.innerText;   // capture before adding buttons
                // Guess a file extension from the ```lang fence, if any
                var ext = "txt";
                if (code) {
                    var m = (code.className || "").match(/language-([a-z0-9]+)/i);
                    if (m) {
                        var map = {python:"py", py:"py", bash:"sh", shell:"sh", sh:"sh",
                                   javascript:"js", js:"js", json:"json", yaml:"yaml", yml:"yaml",
                                   nextflow:"nf", groovy:"groovy", r:"R", text:"txt"};
                        var lang = m[1].toLowerCase();
                        ext = map[lang] || lang;
                    }
                }
                pre.style.position = "relative";
                pre.style.paddingTop = "1.9rem";              // room so buttons don't cover code
                var bar = document.createElement("div");
                bar.style.cssText = "position:absolute;top:4px;right:6px;display:flex;gap:4px;";
                function mkBtn(label) {
                    var b = document.createElement("button");
                    b.type = "button";
                    b.textContent = label;
                    b.style.cssText = "font-size:11px;line-height:1;padding:3px 7px;border:1px solid #ccc;" +
                                      "border-radius:4px;background:#fff;color:#333;cursor:pointer;opacity:0.85;";
                    return b;
                }
                var copyBtn = mkBtn("Copy");
                copyBtn.onclick = function() {
                    var done = function() {
                        copyBtn.textContent = "Copied!";
                        setTimeout(function(){ copyBtn.textContent = "Copy"; }, 1500);
                    };
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        navigator.clipboard.writeText(text).then(done, done);
                    } else {                                   // fallback for non-secure contexts
                        var ta = document.createElement("textarea");
                        ta.value = text;
                        document.body.appendChild(ta);
                        ta.select();
                        try { document.execCommand("copy"); } catch (e) {}
                        document.body.removeChild(ta);
                        done();
                    }
                };
                var dlBtn = mkBtn("Download");
                dlBtn.onclick = function() {
                    var blob = new Blob([text], {type: "text/plain"});
                    var url = URL.createObjectURL(blob);
                    var a = document.createElement("a");
                    a.href = url;
                    a.download = "jawm_snippet." + ext;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                };
                bar.appendChild(copyBtn);
                bar.appendChild(dlBtn);
                pre.appendChild(bar);
            });
        }, 100);
        return '';
    }
    """,
    Output("dummy-scroll", "children"),
    Input("chat-container", "children")
)

# Clientside callback to disable the ASK button and show a spinner immediately when clicked
dashapp.clientside_callback(
    """
    function(n_clicks) {
        // When the button is clicked, disable it and replace its content with a spinner
        var btn = document.getElementById('send-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner-border spinner-border-sm" role="status"><span class="visually-hidden">Loading...</span></div>';
        }
        return '';
    }
    """,
    Output("btn-state-dummy", "children"),
    Input("send-btn", "n_clicks")
)
