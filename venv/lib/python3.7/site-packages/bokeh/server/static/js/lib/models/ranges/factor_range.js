"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const range_1 = require("./range");
const p = require("../../core/properties");
const arrayable_1 = require("../../core/util/arrayable");
const array_1 = require("../../core/util/array");
const types_1 = require("../../core/util/types");
function map_one_level(factors, padding, offset = 0) {
    const mapping = {};
    for (let i = 0; i < factors.length; i++) {
        const factor = factors[i];
        if (factor in mapping)
            throw new Error(`duplicate factor or subfactor: ${factor}`);
        else
            mapping[factor] = { value: 0.5 + i * (1 + padding) + offset };
    }
    return [mapping, (factors.length - 1) * padding];
}
exports.map_one_level = map_one_level;
function map_two_levels(factors, outer_pad, factor_pad, offset = 0) {
    const mapping = {};
    const tops = {};
    const tops_order = [];
    for (const [f0, f1] of factors) {
        if (!(f0 in tops)) {
            tops[f0] = [];
            tops_order.push(f0);
        }
        tops[f0].push(f1);
    }
    let suboffset = offset;
    let total_subpad = 0;
    for (const f0 of tops_order) {
        const n = tops[f0].length;
        const [submap, subpad] = map_one_level(tops[f0], factor_pad, suboffset);
        total_subpad += subpad;
        const subtot = array_1.sum(tops[f0].map((f1) => submap[f1].value));
        mapping[f0] = { value: subtot / n, mapping: submap };
        suboffset += n + outer_pad + subpad;
    }
    return [mapping, tops_order, (tops_order.length - 1) * outer_pad + total_subpad];
}
exports.map_two_levels = map_two_levels;
function map_three_levels(factors, outer_pad, inner_pad, factor_pad, offset = 0) {
    const mapping = {};
    const tops = {};
    const tops_order = [];
    for (const [f0, f1, f2] of factors) {
        if (!(f0 in tops)) {
            tops[f0] = [];
            tops_order.push(f0);
        }
        tops[f0].push([f1, f2]);
    }
    const mids_order = [];
    let suboffset = offset;
    let total_subpad = 0;
    for (const f0 of tops_order) {
        const n = tops[f0].length;
        const [submap, submids_order, subpad] = map_two_levels(tops[f0], inner_pad, factor_pad, suboffset);
        for (const f1 of submids_order)
            mids_order.push([f0, f1]);
        total_subpad += subpad;
        const subtot = array_1.sum(tops[f0].map(([f1]) => submap[f1].value));
        mapping[f0] = { value: subtot / n, mapping: submap };
        suboffset += n + outer_pad + subpad;
    }
    return [mapping, tops_order, mids_order, (tops_order.length - 1) * outer_pad + total_subpad];
}
exports.map_three_levels = map_three_levels;
class FactorRange extends range_1.Range {
    constructor(attrs) {
        super(attrs);
    }
    static init_FactorRange() {
        this.define({
            factors: [p.Array, []],
            factor_padding: [p.Number, 0],
            subgroup_padding: [p.Number, 0.8],
            group_padding: [p.Number, 1.4],
            range_padding: [p.Number, 0],
            range_padding_units: [p.PaddingUnits, "percent"],
            start: [p.Number],
            end: [p.Number],
        });
        this.internal({
            levels: [p.Number],
            mids: [p.Array],
            tops: [p.Array],
            tops_groups: [p.Array],
        });
    }
    get min() {
        return this.start;
    }
    get max() {
        return this.end;
    }
    initialize() {
        super.initialize();
        this._init(true);
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.properties.factors.change, () => this.reset());
        this.connect(this.properties.factor_padding.change, () => this.reset());
        this.connect(this.properties.group_padding.change, () => this.reset());
        this.connect(this.properties.subgroup_padding.change, () => this.reset());
        this.connect(this.properties.range_padding.change, () => this.reset());
        this.connect(this.properties.range_padding_units.change, () => this.reset());
    }
    reset() {
        this._init(false);
        this.change.emit();
    }
    _lookup(x) {
        if (x.length == 1) {
            const m = this._mapping;
            if (!m.hasOwnProperty(x[0])) {
                return NaN;
            }
            return m[x[0]].value;
        }
        else if (x.length == 2) {
            const m = this._mapping;
            if (!m.hasOwnProperty(x[0]) || !m[x[0]].mapping.hasOwnProperty(x[1])) {
                return NaN;
            }
            return m[x[0]].mapping[x[1]].value;
        }
        else if (x.length == 3) {
            const m = this._mapping;
            if (!m.hasOwnProperty(x[0]) || !m[x[0]].mapping.hasOwnProperty(x[1]) || !m[x[0]].mapping[x[1]].mapping.hasOwnProperty(x[2])) {
                return NaN;
            }
            return m[x[0]].mapping[x[1]].mapping[x[2]].value;
        }
        else
            throw new Error("unreachable code");
    }
    // convert a string factor into a synthetic coordinate
    synthetic(x) {
        if (types_1.isNumber(x))
            return x;
        if (types_1.isString(x))
            return this._lookup([x]);
        let offset = 0;
        const off = x[x.length - 1];
        if (types_1.isNumber(off)) {
            offset = off;
            x = x.slice(0, -1);
        }
        return this._lookup(x) + offset;
    }
    // convert an array of string factors into synthetic coordinates
    v_synthetic(xs) {
        return arrayable_1.map(xs, (x) => this.synthetic(x));
    }
    _init(silent) {
        let levels;
        let inside_padding;
        if (array_1.every(this.factors, types_1.isString)) {
            levels = 1;
            [this._mapping, inside_padding] = map_one_level(this.factors, this.factor_padding);
        }
        else if (array_1.every(this.factors, (x) => types_1.isArray(x) && x.length == 2 && types_1.isString(x[0]) && types_1.isString(x[1]))) {
            levels = 2;
            [this._mapping, this.tops, inside_padding] = map_two_levels(this.factors, this.group_padding, this.factor_padding);
        }
        else if (array_1.every(this.factors, (x) => types_1.isArray(x) && x.length == 3 && types_1.isString(x[0]) && types_1.isString(x[1]) && types_1.isString(x[2]))) {
            levels = 3;
            [this._mapping, this.tops, this.mids, inside_padding] = map_three_levels(this.factors, this.group_padding, this.subgroup_padding, this.factor_padding);
        }
        else
            throw new Error("???");
        let start = 0;
        let end = this.factors.length + inside_padding;
        if (this.range_padding_units == "percent") {
            const half_span = (end - start) * this.range_padding / 2;
            start -= half_span;
            end += half_span;
        }
        else {
            start -= this.range_padding;
            end += this.range_padding;
        }
        this.setv({ start, end, levels }, { silent });
        if (this.bounds == "auto")
            this.setv({ bounds: [start, end] }, { silent: true });
    }
}
exports.FactorRange = FactorRange;
FactorRange.__name__ = "FactorRange";
FactorRange.init_FactorRange();
