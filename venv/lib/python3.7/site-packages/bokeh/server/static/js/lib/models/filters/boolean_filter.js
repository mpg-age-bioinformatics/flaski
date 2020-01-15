"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const filter_1 = require("./filter");
const p = require("../../core/properties");
const logging_1 = require("../../core/logging");
const array_1 = require("../../core/util/array");
const types_1 = require("../../core/util/types");
class BooleanFilter extends filter_1.Filter {
    constructor(attrs) {
        super(attrs);
    }
    static init_BooleanFilter() {
        this.define({
            booleans: [p.Array, null],
        });
    }
    compute_indices(source) {
        const booleans = this.booleans;
        if (booleans != null && booleans.length > 0) {
            if (array_1.every(booleans, types_1.isBoolean)) {
                if (booleans.length !== source.get_length()) {
                    logging_1.logger.warn(`BooleanFilter ${this.id}: length of booleans doesn't match data source`);
                }
                return array_1.range(0, booleans.length).filter((i) => booleans[i] === true);
            }
            else {
                logging_1.logger.warn(`BooleanFilter ${this.id}: booleans should be array of booleans, defaulting to no filtering`);
                return null;
            }
        }
        else {
            if (booleans != null && booleans.length == 0)
                logging_1.logger.warn(`BooleanFilter ${this.id}: booleans is empty, defaulting to no filtering`);
            else
                logging_1.logger.warn(`BooleanFilter ${this.id}: booleans was not set, defaulting to no filtering`);
            return null;
        }
    }
}
exports.BooleanFilter = BooleanFilter;
BooleanFilter.__name__ = "BooleanFilter";
BooleanFilter.init_BooleanFilter();
