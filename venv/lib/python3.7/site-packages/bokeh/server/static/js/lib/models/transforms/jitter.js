"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transform_1 = require("./transform");
const factor_range_1 = require("../ranges/factor_range");
const types_1 = require("../../core/util/types");
const p = require("../../core/properties");
const bokeh_math = require("../../core/util/math");
class Jitter extends transform_1.Transform {
    constructor(attrs) {
        super(attrs);
    }
    static init_Jitter() {
        this.define({
            mean: [p.Number, 0],
            width: [p.Number, 1],
            distribution: [p.Distribution, 'uniform'],
            range: [p.Instance],
        });
        this.internal({
            previous_values: [p.Array],
        });
    }
    v_compute(xs0) {
        if (this.previous_values != null && this.previous_values.length == xs0.length)
            return this.previous_values;
        let xs;
        if (this.range instanceof factor_range_1.FactorRange)
            xs = this.range.v_synthetic(xs0);
        else if (types_1.isArrayableOf(xs0, types_1.isNumber))
            xs = xs0;
        else
            throw new Error("unexpected");
        const result = new Float64Array(xs.length);
        for (let i = 0; i < xs.length; i++) {
            const x = xs[i];
            result[i] = this._compute(x);
        }
        this.previous_values = result;
        return result;
    }
    compute(x) {
        if (this.range instanceof factor_range_1.FactorRange)
            return this._compute(this.range.synthetic(x));
        else if (types_1.isNumber(x))
            return this._compute(x);
        else
            throw new Error("unexpected");
    }
    _compute(x) {
        switch (this.distribution) {
            case "uniform":
                return x + this.mean + (bokeh_math.random() - 0.5) * this.width;
            case "normal":
                return x + bokeh_math.rnorm(this.mean, this.width);
        }
    }
}
exports.Jitter = Jitter;
Jitter.__name__ = "Jitter";
Jitter.init_Jitter();
