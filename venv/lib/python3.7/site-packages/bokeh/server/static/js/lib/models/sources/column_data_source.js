"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const columnar_data_source_1 = require("./columnar_data_source");
const has_props_1 = require("../../core/has_props");
const p = require("../../core/properties");
const data_structures_1 = require("../../core/util/data_structures");
const serialization_1 = require("../../core/util/serialization");
const types_1 = require("../../core/util/types");
const typed_array = require("../../core/util/typed_array");
const object_1 = require("../../core/util/object");
const events_1 = require("../../document/events");
//exported for testing
function stream_to_column(col, new_col, rollover) {
    if (types_1.isArray(col)) {
        const result = col.concat(new_col);
        if (rollover != null && result.length > rollover)
            return result.slice(-rollover);
        else
            return result;
    }
    else if (types_1.isTypedArray(col)) {
        const total_len = col.length + new_col.length;
        // handle rollover case for typed arrays
        if (rollover != null && total_len > rollover) {
            const start = total_len - rollover;
            const end = col.length;
            // resize col if it is shorter than the rollover length
            let result;
            if (col.length < rollover) {
                result = new col.constructor(rollover);
                result.set(col, 0);
            }
            else
                result = col;
            // shift values in original col to accommodate new_col
            for (let i = start, endi = end; i < endi; i++) {
                result[i - start] = result[i];
            }
            // update end values in col with new_col
            for (let i = 0, endi = new_col.length; i < endi; i++) {
                result[i + (end - start)] = new_col[i];
            }
            return result;
        }
        else {
            const tmp = new col.constructor(new_col);
            return typed_array.concat(col, tmp);
        }
    }
    else
        throw new Error("unsupported array types");
}
exports.stream_to_column = stream_to_column;
// exported for testing
function slice(ind, length) {
    let start, step, stop;
    if (types_1.isNumber(ind)) {
        start = ind;
        stop = ind + 1;
        step = 1;
    }
    else {
        start = ind.start != null ? ind.start : 0;
        stop = ind.stop != null ? ind.stop : length;
        step = ind.step != null ? ind.step : 1;
    }
    return [start, stop, step];
}
exports.slice = slice;
// exported for testing
function patch_to_column(col, patch, shapes) {
    const patched = new data_structures_1.Set();
    let patched_range = false;
    for (const [ind, val] of patch) {
        // make the single index case look like the length-3 multi-index case
        let item, shape;
        let index;
        let value;
        if (types_1.isArray(ind)) {
            const [i] = ind;
            patched.add(i);
            shape = shapes[i];
            item = col[i];
            value = val;
            // this is basically like NumPy's "newaxis", inserting an empty dimension
            // makes length 2 and 3 multi-index cases uniform, so that the same code
            // can handle both
            if (ind.length === 2) {
                shape = [1, shape[0]];
                index = [ind[0], 0, ind[1]];
            }
            else
                index = ind;
        }
        else {
            if (types_1.isNumber(ind)) {
                value = [val];
                patched.add(ind);
            }
            else {
                value = val;
                patched_range = true;
            }
            index = [0, 0, ind];
            shape = [1, col.length];
            item = col;
        }
        // now this one nested loop handles all cases
        let flat_index = 0;
        const [istart, istop, istep] = slice(index[1], shape[0]);
        const [jstart, jstop, jstep] = slice(index[2], shape[1]);
        for (let i = istart; i < istop; i += istep) {
            for (let j = jstart; j < jstop; j += jstep) {
                if (patched_range) {
                    patched.add(j);
                }
                item[(i * shape[1]) + j] = value[flat_index];
                flat_index++;
            }
        }
    }
    return patched;
}
exports.patch_to_column = patch_to_column;
class ColumnDataSource extends columnar_data_source_1.ColumnarDataSource {
    constructor(attrs) {
        super(attrs);
    }
    static init_ColumnDataSource() {
        this.define({
            data: [p.Any, {}],
        });
    }
    initialize() {
        super.initialize();
        [this.data, this._shapes] = serialization_1.decode_column_data(this.data);
    }
    attributes_as_json(include_defaults = true, value_to_json = ColumnDataSource._value_to_json) {
        const attrs = {};
        const obj = this.serializable_attributes();
        for (const key of object_1.keys(obj)) {
            let value = obj[key];
            if (key === 'data')
                value = serialization_1.encode_column_data(value, this._shapes);
            if (include_defaults)
                attrs[key] = value;
            else if (key in this._set_after_defaults)
                attrs[key] = value;
        }
        return value_to_json("attributes", attrs, this);
    }
    static _value_to_json(key, value, optional_parent_object) {
        if (types_1.isPlainObject(value) && key === 'data')
            return serialization_1.encode_column_data(value, optional_parent_object._shapes); // XXX: unknown vs. any
        else
            return has_props_1.HasProps._value_to_json(key, value, optional_parent_object);
    }
    stream(new_data, rollover, setter_id) {
        const { data } = this;
        for (const k in new_data) {
            data[k] = stream_to_column(data[k], new_data[k], rollover);
        }
        this.setv({ data }, { silent: true });
        this.streaming.emit();
        if (this.document != null) {
            const hint = new events_1.ColumnsStreamedEvent(this.document, this.ref(), new_data, rollover);
            this.document._notify_change(this, 'data', null, null, { setter_id, hint });
        }
    }
    patch(patches, setter_id) {
        const { data } = this;
        let patched = new data_structures_1.Set();
        for (const k in patches) {
            const patch = patches[k];
            patched = patched.union(patch_to_column(data[k], patch, this._shapes[k]));
        }
        this.setv({ data }, { silent: true });
        this.patching.emit(patched.values);
        if (this.document != null) {
            const hint = new events_1.ColumnsPatchedEvent(this.document, this.ref(), patches);
            this.document._notify_change(this, 'data', null, null, { setter_id, hint });
        }
    }
}
exports.ColumnDataSource = ColumnDataSource;
ColumnDataSource.__name__ = "ColumnDataSource";
ColumnDataSource.init_ColumnDataSource();
