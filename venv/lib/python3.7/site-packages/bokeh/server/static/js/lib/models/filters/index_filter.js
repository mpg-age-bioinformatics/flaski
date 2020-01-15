"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const filter_1 = require("./filter");
const p = require("../../core/properties");
const logging_1 = require("../../core/logging");
const types_1 = require("../../core/util/types");
const array_1 = require("../../core/util/array");
class IndexFilter extends filter_1.Filter {
    constructor(attrs) {
        super(attrs);
    }
    static init_IndexFilter() {
        this.define({
            indices: [p.Array, null],
        });
    }
    compute_indices(_source) {
        if (this.indices != null && this.indices.length >= 0) {
            if (array_1.every(this.indices, types_1.isInteger))
                return this.indices;
            else {
                logging_1.logger.warn(`IndexFilter ${this.id}: indices should be array of integers, defaulting to no filtering`);
                return null;
            }
        }
        else {
            logging_1.logger.warn(`IndexFilter ${this.id}: indices was not set, defaulting to no filtering`);
            return null;
        }
    }
}
exports.IndexFilter = IndexFilter;
IndexFilter.__name__ = "IndexFilter";
IndexFilter.init_IndexFilter();
