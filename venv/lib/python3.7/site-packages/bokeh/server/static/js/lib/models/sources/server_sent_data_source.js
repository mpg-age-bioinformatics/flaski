"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const web_data_source_1 = require("./web_data_source");
class ServerSentDataSource extends web_data_source_1.WebDataSource {
    constructor(attrs) {
        super(attrs);
        this.initialized = false;
    }
    destroy() {
        super.destroy();
    }
    setup() {
        if (!this.initialized) {
            this.initialized = true;
            const source = new EventSource(this.data_url);
            source.onmessage = (event) => {
                this.load_data(JSON.parse(event.data), this.mode, this.max_size);
            };
        }
    }
}
exports.ServerSentDataSource = ServerSentDataSource;
ServerSentDataSource.__name__ = "ServerSentDataSource";
