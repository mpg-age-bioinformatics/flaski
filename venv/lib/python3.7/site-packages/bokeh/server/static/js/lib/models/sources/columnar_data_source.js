"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const data_source_1 = require("./data_source");
const signaling_1 = require("../../core/signaling");
const logging_1 = require("../../core/logging");
const selection_manager_1 = require("../../core/selection_manager");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
const array_1 = require("../../core/util/array");
const object_1 = require("../../core/util/object");
const selection_1 = require("../selections/selection");
const interaction_policy_1 = require("../selections/interaction_policy");
class ColumnarDataSource extends data_source_1.DataSource {
    constructor(attrs) {
        super(attrs);
    }
    get_array(key) {
        let column = this.data[key];
        if (column == null)
            this.data[key] = column = [];
        else if (!types_1.isArray(column))
            this.data[key] = column = Array.from(column);
        return column;
    }
    static init_ColumnarDataSource() {
        this.define({
            selection_policy: [p.Instance, () => new interaction_policy_1.UnionRenderers()],
        });
        this.internal({
            selection_manager: [p.Instance, (self) => new selection_manager_1.SelectionManager({ source: self })],
            inspected: [p.Instance, () => new selection_1.Selection()],
            _shapes: [p.Any, {}],
        });
    }
    initialize() {
        super.initialize();
        this._select = new signaling_1.Signal0(this, "select");
        this.inspect = new signaling_1.Signal(this, "inspect"); // XXX: <[indices, tool, renderer-view, source, data], this>
        this.streaming = new signaling_1.Signal0(this, "streaming");
        this.patching = new signaling_1.Signal(this, "patching");
    }
    get_column(colname) {
        const column = this.data[colname];
        return column != null ? column : null;
    }
    columns() {
        // return the column names in this data source
        return object_1.keys(this.data);
    }
    get_length(soft = true) {
        const lengths = array_1.uniq(object_1.values(this.data).map((v) => v.length));
        switch (lengths.length) {
            case 0: {
                return null; // XXX: don't guess, treat on case-by-case basis
            }
            case 1: {
                return lengths[0];
            }
            default: {
                const msg = "data source has columns of inconsistent lengths";
                if (soft) {
                    logging_1.logger.warn(msg);
                    return lengths.sort()[0];
                }
                else
                    throw new Error(msg);
            }
        }
    }
    get_indices() {
        const length = this.get_length();
        return array_1.range(0, length != null ? length : 1);
        //TODO: returns [0] when no data, should it?
    }
    clear() {
        const empty = {};
        for (const col of this.columns()) {
            empty[col] = new this.data[col].constructor(0);
        }
        this.data = empty;
    }
}
exports.ColumnarDataSource = ColumnarDataSource;
ColumnarDataSource.__name__ = "ColumnarDataSource";
ColumnarDataSource.init_ColumnarDataSource();
