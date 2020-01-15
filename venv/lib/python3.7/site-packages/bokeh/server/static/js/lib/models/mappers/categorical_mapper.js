"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const arrayable_1 = require("../../core/util/arrayable");
const types_1 = require("../../core/util/types");
function _cat_equals(a, b) {
    if (a.length != b.length)
        return false;
    for (let i = 0, end = a.length; i < end; i++) {
        if (a[i] !== b[i])
            return false;
    }
    return true;
}
exports._cat_equals = _cat_equals;
function cat_v_compute(data, factors, targets, values, start, end, extra_value) {
    for (let i = 0, N = data.length; i < N; i++) {
        let d = data[i];
        let key;
        if (types_1.isString(d))
            key = arrayable_1.index_of(factors, d);
        else {
            if (start != null) {
                if (end != null)
                    d = d.slice(start, end);
                else
                    d = d.slice(start);
            }
            else if (end != null)
                d = d.slice(0, end);
            if (d.length == 1)
                key = arrayable_1.index_of(factors, d[0]);
            else
                key = arrayable_1.find_index(factors, (x) => _cat_equals(x, d));
        }
        let value;
        if (key < 0 || key >= targets.length)
            value = extra_value;
        else
            value = targets[key];
        values[i] = value;
    }
}
exports.cat_v_compute = cat_v_compute;
