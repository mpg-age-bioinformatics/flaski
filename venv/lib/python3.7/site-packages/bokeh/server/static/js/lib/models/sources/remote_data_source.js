"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const web_data_source_1 = require("./web_data_source");
const p = require("../../core/properties");
class RemoteDataSource extends web_data_source_1.WebDataSource {
    constructor(attrs) {
        super(attrs);
    }
    get_column(colname) {
        const column = this.data[colname];
        return column != null ? column : [];
    }
    initialize() {
        super.initialize();
        this.setup();
    }
    static init_RemoteDataSource() {
        this.define({
            polling_interval: [p.Number],
        });
    }
}
exports.RemoteDataSource = RemoteDataSource;
RemoteDataSource.__name__ = "RemoteDataSource";
RemoteDataSource.init_RemoteDataSource();
