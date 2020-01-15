"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
const array_1 = require("../../core/util/array");
const logging_1 = require("../../core/logging");
class Filter extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Filter() {
        this.define({
            filter: [p.Array, null],
        });
    }
    compute_indices(_source) {
        const filter = this.filter;
        if (filter != null && filter.length >= 0) {
            if (types_1.isArrayOf(filter, types_1.isBoolean)) {
                return array_1.range(0, filter.length).filter((i) => filter[i] === true);
            }
            if (types_1.isArrayOf(filter, types_1.isInteger)) {
                return filter;
            }
            logging_1.logger.warn(`Filter ${this.id}: filter should either be array of only booleans or only integers, defaulting to no filtering`);
            return null;
        }
        else {
            logging_1.logger.warn(`Filter ${this.id}: filter was not set to be an array, defaulting to no filtering`);
            return null;
        }
    }
}
exports.Filter = Filter;
Filter.__name__ = "Filter";
Filter.init_Filter();
