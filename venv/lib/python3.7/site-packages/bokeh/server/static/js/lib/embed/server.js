"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const connection_1 = require("../client/connection");
const logging_1 = require("../core/logging");
const standalone_1 = require("./standalone");
// @internal
function _get_ws_url(app_path, absolute_url) {
    let protocol = 'ws:';
    if (window.location.protocol == 'https:')
        protocol = 'wss:';
    let loc;
    if (absolute_url != null) {
        loc = document.createElement('a');
        loc.href = absolute_url;
    }
    else
        loc = window.location;
    if (app_path != null) {
        if (app_path == "/")
            app_path = "";
    }
    else
        app_path = loc.pathname.replace(/\/+$/, '');
    return protocol + '//' + loc.host + app_path + '/ws';
}
exports._get_ws_url = _get_ws_url;
// map { websocket url to map { session id to promise of ClientSession } }
const _sessions = {};
function _get_session(websocket_url, session_id, args_string) {
    if (!(websocket_url in _sessions))
        _sessions[websocket_url] = {};
    const subsessions = _sessions[websocket_url];
    if (!(session_id in subsessions))
        subsessions[session_id] = connection_1.pull_session(websocket_url, session_id, args_string);
    return subsessions[session_id];
}
// Fill element with the roots from session_id
function add_document_from_session(websocket_url, session_id, element, roots = {}, use_for_title = false) {
    const args_string = window.location.search.substr(1);
    const promise = _get_session(websocket_url, session_id, args_string);
    return promise.then((session) => {
        return standalone_1.add_document_standalone(session.document, element, roots, use_for_title);
    }, (error) => {
        logging_1.logger.error(`Failed to load Bokeh session ${session_id}: ${error}`);
        throw error;
    });
}
exports.add_document_from_session = add_document_from_session;
