"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const categorical_scale_1 = require("../scales/categorical_scale");
const linear_scale_1 = require("../scales/linear_scale");
const log_scale_1 = require("../scales/log_scale");
const range1d_1 = require("../ranges/range1d");
const data_range1d_1 = require("../ranges/data_range1d");
const factor_range_1 = require("../ranges/factor_range");
const layout_1 = require("../../core/layout");
class CartesianFrame extends layout_1.LayoutItem {
    constructor(x_scale, y_scale, x_range, y_range, extra_x_ranges = {}, extra_y_ranges = {}) {
        super();
        this.x_scale = x_scale;
        this.y_scale = y_scale;
        this.x_range = x_range;
        this.y_range = y_range;
        this.extra_x_ranges = extra_x_ranges;
        this.extra_y_ranges = extra_y_ranges;
        this._configure_scales();
    }
    map_to_screen(x, y, x_name = "default", y_name = "default") {
        const sx = this.xscales[x_name].v_compute(x);
        const sy = this.yscales[y_name].v_compute(y);
        return [sx, sy];
    }
    _get_ranges(range, extra_ranges) {
        const ranges = {};
        ranges.default = range;
        if (extra_ranges != null) {
            for (const name in extra_ranges)
                ranges[name] = extra_ranges[name];
        }
        return ranges;
    }
    /*protected*/ _get_scales(scale, ranges, frame_range) {
        const scales = {};
        for (const name in ranges) {
            const range = ranges[name];
            if (range instanceof data_range1d_1.DataRange1d || range instanceof range1d_1.Range1d) {
                if (!(scale instanceof log_scale_1.LogScale) && !(scale instanceof linear_scale_1.LinearScale))
                    throw new Error(`Range ${range.type} is incompatible is Scale ${scale.type}`);
                // XXX: special case because CategoricalScale is a subclass of LinearScale, should be removed in future
                if (scale instanceof categorical_scale_1.CategoricalScale)
                    throw new Error(`Range ${range.type} is incompatible is Scale ${scale.type}`);
            }
            if (range instanceof factor_range_1.FactorRange) {
                if (!(scale instanceof categorical_scale_1.CategoricalScale))
                    throw new Error(`Range ${range.type} is incompatible is Scale ${scale.type}`);
            }
            if (scale instanceof log_scale_1.LogScale && range instanceof data_range1d_1.DataRange1d)
                range.scale_hint = "log";
            const s = scale.clone();
            s.setv({ source_range: range, target_range: frame_range });
            scales[name] = s;
        }
        return scales;
    }
    _configure_frame_ranges() {
        // data to/from screen space transform (left-bottom <-> left-top origin)
        this._h_target = new range1d_1.Range1d({ start: this._left.value, end: this._right.value });
        this._v_target = new range1d_1.Range1d({ start: this._bottom.value, end: this._top.value });
    }
    _configure_scales() {
        this._configure_frame_ranges();
        this._x_ranges = this._get_ranges(this.x_range, this.extra_x_ranges);
        this._y_ranges = this._get_ranges(this.y_range, this.extra_y_ranges);
        this._xscales = this._get_scales(this.x_scale, this._x_ranges, this._h_target);
        this._yscales = this._get_scales(this.y_scale, this._y_ranges, this._v_target);
    }
    _update_scales() {
        this._configure_frame_ranges();
        for (const name in this._xscales) {
            const scale = this._xscales[name];
            scale.target_range = this._h_target;
        }
        for (const name in this._yscales) {
            const scale = this._yscales[name];
            scale.target_range = this._v_target;
        }
    }
    _set_geometry(outer, inner) {
        super._set_geometry(outer, inner);
        this._update_scales();
    }
    get x_ranges() {
        return this._x_ranges;
    }
    get y_ranges() {
        return this._y_ranges;
    }
    get xscales() {
        return this._xscales;
    }
    get yscales() {
        return this._yscales;
    }
}
exports.CartesianFrame = CartesianFrame;
CartesianFrame.__name__ = "CartesianFrame";
