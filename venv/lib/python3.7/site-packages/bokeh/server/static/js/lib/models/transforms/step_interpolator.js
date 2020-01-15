"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const interpolator_1 = require("./interpolator");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
class StepInterpolator extends interpolator_1.Interpolator {
    constructor(attrs) {
        super(attrs);
    }
    static init_StepInterpolator() {
        this.define({
            mode: [p.StepMode, "after"],
        });
    }
    compute(x) {
        this.sort(false);
        if (this.clip) {
            if (x < this._x_sorted[0] || x > this._x_sorted[this._x_sorted.length - 1])
                return NaN;
        }
        else {
            if (x < this._x_sorted[0])
                return this._y_sorted[0];
            if (x > this._x_sorted[this._x_sorted.length - 1])
                return this._y_sorted[this._y_sorted.length - 1];
        }
        let ind;
        switch (this.mode) {
            case "after": {
                ind = array_1.find_last_index(this._x_sorted, num => x >= num);
                break;
            }
            case "before": {
                ind = array_1.find_index(this._x_sorted, num => x <= num);
                break;
            }
            case "center": {
                const diffs = this._x_sorted.map((tx) => Math.abs(tx - x));
                const mdiff = array_1.min(diffs);
                ind = array_1.find_index(diffs, num => mdiff === num);
                break;
            }
            default:
                throw new Error(`unknown mode: ${this.mode}`);
        }
        return ind != -1 ? this._y_sorted[ind] : NaN;
    }
}
exports.StepInterpolator = StepInterpolator;
StepInterpolator.__name__ = "StepInterpolator";
StepInterpolator.init_StepInterpolator();
