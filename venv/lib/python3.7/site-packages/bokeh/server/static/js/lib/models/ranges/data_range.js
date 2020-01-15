"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const range_1 = require("./range");
const p = require("../../core/properties");
class DataRange extends range_1.Range {
    constructor(attrs) {
        super(attrs);
    }
    static init_DataRange() {
        this.define({
            names: [p.Array, []],
            renderers: [p.Array, []],
        });
    }
}
exports.DataRange = DataRange;
DataRange.__name__ = "DataRange";
DataRange.init_DataRange();
