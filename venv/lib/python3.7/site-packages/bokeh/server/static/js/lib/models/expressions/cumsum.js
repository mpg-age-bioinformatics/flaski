"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const expression_1 = require("./expression");
const p = require("../../core/properties");
class CumSum extends expression_1.Expression {
    constructor(attrs) {
        super(attrs);
    }
    static init_CumSum() {
        this.define({
            field: [p.String],
            include_zero: [p.Boolean, false],
        });
    }
    _v_compute(source) {
        const result = new Float64Array(source.get_length() || 0);
        const col = source.data[this.field];
        const offset = this.include_zero ? 1 : 0;
        result[0] = this.include_zero ? 0 : col[0];
        for (let i = 1; i < result.length; i++) {
            result[i] = result[i - 1] + col[i - offset];
        }
        return result;
    }
}
exports.CumSum = CumSum;
CumSum.__name__ = "CumSum";
CumSum.init_CumSum();
