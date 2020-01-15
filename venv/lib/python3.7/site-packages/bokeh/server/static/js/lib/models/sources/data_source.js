"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const selection_1 = require("../selections/selection");
const p = require("../../core/properties");
class DataSource extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_DataSource() {
        this.define({
            selected: [p.Instance, () => new selection_1.Selection()],
            callback: [p.Any],
        });
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.selected.change, () => {
            if (this.callback != null)
                this.callback.execute(this);
        });
    }
}
exports.DataSource = DataSource;
DataSource.__name__ = "DataSource";
DataSource.init_DataSource();
