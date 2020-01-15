"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const logging_1 = require("../core/logging");
const document_1 = require("../document");
const message_1 = require("../protocol/message");
const receiver_1 = require("../protocol/receiver");
const session_1 = require("./session");
exports.DEFAULT_SERVER_WEBSOCKET_URL = "ws://localhost:5006/ws";
exports.DEFAULT_SESSION_ID = "default";
let _connection_count = 0;
class ClientConnection {
    constructor(url = exports.DEFAULT_SERVER_WEBSOCKET_URL, id = exports.DEFAULT_SESSION_ID, args_string = null, _on_have_session_hook = null, _on_closed_permanently_hook = null) {
        this.url = url;
        this.id = id;
        this.args_string = args_string;
        this._on_have_session_hook = _on_have_session_hook;
        this._on_closed_permanently_hook = _on_closed_permanently_hook;
        this._number = _connection_count++;
        this.socket = null;
        this.session = null;
        this.closed_permanently = false;
        this._current_handler = null;
        this._pending_ack = null; // null or [resolve,reject]
        this._pending_replies = {}; // map reqid to [resolve,reject]
        this._pending_messages = [];
        this._receiver = new receiver_1.Receiver();
        logging_1.logger.debug(`Creating websocket ${this._number} to '${this.url}' session '${this.id}'`);
    }
    connect() {
        if (this.closed_permanently)
            return Promise.reject(new Error("Cannot connect() a closed ClientConnection"));
        if (this.socket != null)
            return Promise.reject(new Error("Already connected"));
        this._pending_replies = {};
        this._current_handler = null;
        try {
            let versioned_url = `${this.url}?bokeh-protocol-version=1.0&bokeh-session-id=${this.id}`;
            if (this.args_string != null && this.args_string.length > 0)
                versioned_url += `&${this.args_string}`;
            this.socket = new WebSocket(versioned_url);
            return new Promise((resolve, reject) => {
                // "arraybuffer" gives us binary data we can look at;
                // if we just needed an opaque blob we could use "blob"
                this.socket.binaryType = "arraybuffer";
                this.socket.onopen = () => this._on_open(resolve, reject);
                this.socket.onmessage = (event) => this._on_message(event);
                this.socket.onclose = (event) => this._on_close(event);
                this.socket.onerror = () => this._on_error(reject);
            });
        }
        catch (error) {
            logging_1.logger.error(`websocket creation failed to url: ${this.url}`);
            logging_1.logger.error(` - ${error}`);
            return Promise.reject(error);
        }
    }
    close() {
        if (!this.closed_permanently) {
            logging_1.logger.debug(`Permanently closing websocket connection ${this._number}`);
            this.closed_permanently = true;
            if (this.socket != null)
                this.socket.close(1000, `close method called on ClientConnection ${this._number}`);
            this.session._connection_closed();
            if (this._on_closed_permanently_hook != null) {
                this._on_closed_permanently_hook();
                this._on_closed_permanently_hook = null;
            }
        }
    }
    _schedule_reconnect(milliseconds) {
        const retry = () => {
            // TODO commented code below until we fix reconnection to repull
            // the document when required. Otherwise, we get a lot of
            // confusing errors that are causing trouble when debugging.
            /*
            if (this.closed_permanently) {
            */
            if (!this.closed_permanently)
                logging_1.logger.info(`Websocket connection ${this._number} disconnected, will not attempt to reconnect`);
            return;
            /*
            } else {
              logger.debug(`Attempting to reconnect websocket ${this._number}`)
              this.connect()
            }
            */
        };
        setTimeout(retry, milliseconds);
    }
    send(message) {
        if (this.socket == null)
            throw new Error(`not connected so cannot send ${message}`);
        message.send(this.socket);
    }
    send_with_reply(message) {
        const promise = new Promise((resolve, reject) => {
            this._pending_replies[message.msgid()] = [resolve, reject];
            this.send(message);
        });
        return promise.then((message) => {
            if (message.msgtype() === "ERROR")
                throw new Error(`Error reply ${message.content.text}`);
            else
                return message;
        }, (error) => {
            throw error;
        });
    }
    _pull_doc_json() {
        const message = message_1.Message.create("PULL-DOC-REQ", {});
        const promise = this.send_with_reply(message);
        return promise.then((reply) => {
            if (!('doc' in reply.content))
                throw new Error("No 'doc' field in PULL-DOC-REPLY");
            return reply.content.doc;
        }, (error) => {
            throw error;
        });
    }
    _repull_session_doc() {
        if (this.session == null)
            logging_1.logger.debug("Pulling session for first time");
        else
            logging_1.logger.debug("Repulling session");
        this._pull_doc_json().then((doc_json) => {
            if (this.session == null) {
                if (this.closed_permanently)
                    logging_1.logger.debug("Got new document after connection was already closed");
                else {
                    const document = document_1.Document.from_json(doc_json);
                    // Constructing models changes some of their attributes, we deal with that
                    // here. This happens when models set attributes during construction
                    // or initialization.
                    const patch = document_1.Document._compute_patch_since_json(doc_json, document);
                    if (patch.events.length > 0) {
                        logging_1.logger.debug(`Sending ${patch.events.length} changes from model construction back to server`);
                        const patch_message = message_1.Message.create('PATCH-DOC', {}, patch);
                        this.send(patch_message);
                    }
                    this.session = new session_1.ClientSession(this, document, this.id);
                    for (const msg of this._pending_messages) {
                        this.session.handle(msg);
                    }
                    this._pending_messages = [];
                    logging_1.logger.debug("Created a new session from new pulled doc");
                    if (this._on_have_session_hook != null) {
                        this._on_have_session_hook(this.session);
                        this._on_have_session_hook = null;
                    }
                }
            }
            else {
                this.session.document.replace_with_json(doc_json);
                logging_1.logger.debug("Updated existing session with new pulled doc");
            }
        }, (error) => {
            // handling the error here is useless because we wouldn't
            // get errors from the resolve handler above, so see
            // the catch below instead
            throw error;
        }).catch((error) => {
            if (console.trace != null)
                console.trace(error);
            logging_1.logger.error(`Failed to repull session ${error}`);
        });
    }
    _on_open(resolve, reject) {
        logging_1.logger.info(`Websocket connection ${this._number} is now open`);
        this._pending_ack = [resolve, reject];
        this._current_handler = (message) => {
            this._awaiting_ack_handler(message);
        };
    }
    _on_message(event) {
        if (this._current_handler == null)
            logging_1.logger.error("Got a message with no current handler set");
        try {
            this._receiver.consume(event.data);
        }
        catch (e) {
            this._close_bad_protocol(e.toString());
        }
        if (this._receiver.message == null)
            return;
        const msg = this._receiver.message;
        const problem = msg.problem();
        if (problem != null)
            this._close_bad_protocol(problem);
        this._current_handler(msg);
    }
    _on_close(event) {
        logging_1.logger.info(`Lost websocket ${this._number} connection, ${event.code} (${event.reason})`);
        this.socket = null;
        if (this._pending_ack != null) {
            this._pending_ack[1](new Error(`Lost websocket connection, ${event.code} (${event.reason})`));
            this._pending_ack = null;
        }
        const pop_pending = () => {
            for (const reqid in this._pending_replies) {
                const promise_funcs = this._pending_replies[reqid];
                delete this._pending_replies[reqid];
                return promise_funcs;
            }
            return null;
        };
        let promise_funcs = pop_pending();
        while (promise_funcs != null) {
            promise_funcs[1]("Disconnected");
            promise_funcs = pop_pending();
        }
        if (!this.closed_permanently)
            this._schedule_reconnect(2000);
    }
    _on_error(reject) {
        logging_1.logger.debug(`Websocket error on socket ${this._number}`);
        reject(new Error("Could not open websocket"));
    }
    _close_bad_protocol(detail) {
        logging_1.logger.error(`Closing connection: ${detail}`);
        if (this.socket != null)
            this.socket.close(1002, detail); // 1002 = protocol error
    }
    _awaiting_ack_handler(message) {
        if (message.msgtype() === "ACK") {
            this._current_handler = (message) => this._steady_state_handler(message);
            // Reload any sessions
            this._repull_session_doc();
            if (this._pending_ack != null) {
                this._pending_ack[0](this);
                this._pending_ack = null;
            }
        }
        else
            this._close_bad_protocol("First message was not an ACK");
    }
    _steady_state_handler(message) {
        if (message.reqid() in this._pending_replies) {
            const promise_funcs = this._pending_replies[message.reqid()];
            delete this._pending_replies[message.reqid()];
            promise_funcs[0](message);
        }
        else if (this.session) {
            this.session.handle(message);
        }
        else {
            this._pending_messages.push(message);
        }
    }
}
exports.ClientConnection = ClientConnection;
ClientConnection.__name__ = "ClientConnection";
// Returns a promise of a ClientSession
// The returned promise has a close() method in case you want to close before
// getting a session; session.close() works too once you have a session.
function pull_session(url, session_id, args_string) {
    const promise = new Promise((resolve, reject) => {
        const connection = new ClientConnection(url, session_id, args_string, (session) => {
            try {
                resolve(session);
            }
            catch (error) {
                logging_1.logger.error(`Promise handler threw an error, closing session ${error}`);
                session.close();
                throw error;
            }
        }, () => {
            // we rely on reject() as a no-op if we already resolved
            reject(new Error("Connection was closed before we successfully pulled a session"));
        });
        connection.connect().then((_) => undefined, (error) => {
            logging_1.logger.error(`Failed to connect to Bokeh server ${error}`);
            throw error;
        });
    });
    return promise;
}
exports.pull_session = pull_session;
