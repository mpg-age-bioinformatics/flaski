"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transforms_1 = require("../transforms");
const p = require("../../core/properties");
class Scale extends transforms_1.Transform {
    constructor(attrs) {
        super(attrs);
    }
    static init_Scale() {
        this.internal({
            source_range: [p.Any],
            target_range: [p.Any],
        });
    }
    r_compute(x0, x1) {
        if (this.target_range.is_reversed)
            return [this.compute(x1), this.compute(x0)];
        else
            return [this.compute(x0), this.compute(x1)];
    }
    r_invert(sx0, sx1) {
        if (this.target_range.is_reversed)
            return [this.invert(sx1), this.invert(sx0)];
        else
            return [this.invert(sx0), this.invert(sx1)];
    }
}
exports.Scale = Scale;
Scale.__name__ = "Scale";
Scale.init_Scale();
