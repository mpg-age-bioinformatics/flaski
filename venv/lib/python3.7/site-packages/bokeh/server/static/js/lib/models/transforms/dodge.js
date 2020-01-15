"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transform_1 = require("./transform");
const factor_range_1 = require("../ranges/factor_range");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
class Dodge extends transform_1.Transform {
    constructor(attrs) {
        super(attrs);
    }
    static init_Dodge() {
        this.define({
            value: [p.Number, 0],
            range: [p.Instance],
        });
    }
    // XXX: this is repeated in ./jitter.ts
    v_compute(xs0) {
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
        return x + this.value;
    }
}
exports.Dodge = Dodge;
Dodge.__name__ = "Dodge";
Dodge.init_Dodge();
