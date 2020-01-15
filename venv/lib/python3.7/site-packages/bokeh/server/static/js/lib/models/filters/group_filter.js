"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const filter_1 = require("./filter");
const p = require("../../core/properties");
const logging_1 = require("../../core/logging");
const array_1 = require("../../core/util/array");
class GroupFilter extends filter_1.Filter {
    constructor(attrs) {
        super(attrs);
        this.indices = null;
    }
    static init_GroupFilter() {
        this.define({
            column_name: [p.String],
            group: [p.String],
        });
    }
    compute_indices(source) {
        const column = source.get_column(this.column_name);
        if (column == null) {
            logging_1.logger.warn("group filter: groupby column not found in data source");
            return null;
        }
        else {
            this.indices = array_1.range(0, source.get_length() || 0).filter((i) => column[i] === this.group);
            if (this.indices.length === 0) {
                logging_1.logger.warn(`group filter: group '${this.group}' did not match any values in column '${this.column_name}'`);
            }
            return this.indices;
        }
    }
}
exports.GroupFilter = GroupFilter;
GroupFilter.__name__ = "GroupFilter";
GroupFilter.init_GroupFilter();
