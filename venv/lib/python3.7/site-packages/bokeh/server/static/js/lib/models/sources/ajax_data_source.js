"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const remote_data_source_1 = require("./remote_data_source");
const logging_1 = require("../../core/logging");
const p = require("../../core/properties");
class AjaxDataSource extends remote_data_source_1.RemoteDataSource {
    constructor(attrs) {
        super(attrs);
        this.initialized = false;
    }
    static init_AjaxDataSource() {
        this.define({
            content_type: [p.String, 'application/json'],
            http_headers: [p.Any, {}],
            method: [p.HTTPMethod, 'POST'],
            if_modified: [p.Boolean, false],
        });
    }
    destroy() {
        if (this.interval != null)
            clearInterval(this.interval);
        super.destroy();
    }
    setup() {
        if (!this.initialized) {
            this.initialized = true;
            this.get_data(this.mode);
            if (this.polling_interval) {
                const callback = () => this.get_data(this.mode, this.max_size, this.if_modified);
                this.interval = setInterval(callback, this.polling_interval);
            }
        }
    }
    get_data(mode, max_size = 0, _if_modified = false) {
        const xhr = this.prepare_request();
        // TODO: if_modified
        xhr.addEventListener("load", () => this.do_load(xhr, mode, max_size));
        xhr.addEventListener("error", () => this.do_error(xhr));
        xhr.send();
    }
    prepare_request() {
        const xhr = new XMLHttpRequest();
        xhr.open(this.method, this.data_url, true);
        xhr.withCredentials = false;
        xhr.setRequestHeader("Content-Type", this.content_type);
        const http_headers = this.http_headers;
        for (const name in http_headers) {
            const value = http_headers[name];
            xhr.setRequestHeader(name, value);
        }
        return xhr;
    }
    do_load(xhr, mode, max_size) {
        if (xhr.status === 200) {
            const raw_data = JSON.parse(xhr.responseText);
            this.load_data(raw_data, mode, max_size);
        }
    }
    do_error(xhr) {
        logging_1.logger.error(`Failed to fetch JSON from ${this.data_url} with code ${xhr.status}`);
    }
}
exports.AjaxDataSource = AjaxDataSource;
AjaxDataSource.__name__ = "AjaxDataSource";
AjaxDataSource.init_AjaxDataSource();
