"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transform_1 = require("./transform");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
const types_1 = require("../../core/util/types");
class Interpolator extends transform_1.Transform {
    constructor(attrs) {
        super(attrs);
        this._sorted_dirty = true;
    }
    static init_Interpolator() {
        this.define({
            x: [p.Any],
            y: [p.Any],
            data: [p.Any],
            clip: [p.Boolean, true],
        });
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.change, () => this._sorted_dirty = true);
    }
    v_compute(xs) {
        const result = new Float64Array(xs.length);
        for (let i = 0; i < xs.length; i++) {
            const x = xs[i];
            result[i] = this.compute(x);
        }
        return result;
    }
    sort(descending = false) {
        if (!this._sorted_dirty)
            return;
        let tsx;
        let tsy;
        if (types_1.isString(this.x) && types_1.isString(this.y) && this.data != null) {
            const column_names = this.data.columns();
            if (!array_1.includes(column_names, this.x))
                throw new Error("The x parameter does not correspond to a valid column name defined in the data parameter");
            if (!array_1.includes(column_names, this.y))
                throw new Error("The y parameter does not correspond to a valid column name defined in the data parameter");
            tsx = this.data.get_column(this.x);
            tsy = this.data.get_column(this.y);
        }
        else if (types_1.isArray(this.x) && types_1.isArray(this.y)) {
            tsx = this.x;
            tsy = this.y;
        }
        else {
            throw new Error("parameters 'x' and 'y' must be both either string fields or arrays");
        }
        if (tsx.length !== tsy.length)
            throw new Error("The length for x and y do not match");
        if (tsx.length < 2)
            throw new Error("x and y must have at least two elements to support interpolation");
        // The following sorting code is referenced from:
        // http://stackoverflow.com/questions/11499268/sort-two-arrays-the-same-way
        const list = [];
        for (const j in tsx) {
            list.push({ x: tsx[j], y: tsy[j] });
        }
        if (descending)
            list.sort((a, b) => a.x > b.x ? -1 : (a.x == b.x ? 0 : 1));
        else
            list.sort((a, b) => a.x < b.x ? -1 : (a.x == b.x ? 0 : 1));
        this._x_sorted = [];
        this._y_sorted = [];
        for (const { x, y } of list) {
            this._x_sorted.push(x);
            this._y_sorted.push(y);
        }
        this._sorted_dirty = false;
    }
}
exports.Interpolator = Interpolator;
Interpolator.__name__ = "Interpolator";
Interpolator.init_Interpolator();
