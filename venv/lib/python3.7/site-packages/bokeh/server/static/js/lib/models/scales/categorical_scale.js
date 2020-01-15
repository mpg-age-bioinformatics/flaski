"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const linear_scale_1 = require("./linear_scale");
class CategoricalScale extends linear_scale_1.LinearScale {
    constructor(attrs) {
        super(attrs);
    }
    compute(x) {
        return super.compute(this.source_range.synthetic(x));
    }
    v_compute(xs) {
        return super.v_compute(this.source_range.v_synthetic(xs));
    }
}
exports.CategoricalScale = CategoricalScale;
CategoricalScale.__name__ = "CategoricalScale";
