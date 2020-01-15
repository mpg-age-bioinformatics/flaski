"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const range_1 = require("./range");
const p = require("../../core/properties");
class Range1d extends range_1.Range {
    constructor(attrs) {
        super(attrs);
    }
    static init_Range1d() {
        this.define({
            start: [p.Number, 0],
            end: [p.Number, 1],
            reset_start: [p.Number],
            reset_end: [p.Number],
        });
    }
    _set_auto_bounds() {
        if (this.bounds == 'auto') {
            const min = Math.min(this.reset_start, this.reset_end);
            const max = Math.max(this.reset_start, this.reset_end);
            this.setv({ bounds: [min, max] }, { silent: true });
        }
    }
    initialize() {
        super.initialize();
        if (this.reset_start == null) {
            this.reset_start = this.start;
        }
        if (this.reset_end == null) {
            this.reset_end = this.end;
        }
        this._set_auto_bounds();
    }
    get min() {
        return Math.min(this.start, this.end);
    }
    get max() {
        return Math.max(this.start, this.end);
    }
    reset() {
        this._set_auto_bounds();
        if (this.start != this.reset_start || this.end != this.reset_end)
            this.setv({ start: this.reset_start, end: this.reset_end });
        else
            this.change.emit();
    }
}
exports.Range1d = Range1d;
Range1d.__name__ = "Range1d";
Range1d.init_Range1d();
