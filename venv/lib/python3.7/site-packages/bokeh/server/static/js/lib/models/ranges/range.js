"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
class Range extends model_1.Model {
    constructor(attrs) {
        super(attrs);
        this.have_updated_interactively = false;
    }
    static init_Range() {
        this.define({
            callback: [p.Any],
            bounds: [p.Any],
            min_interval: [p.Any],
            max_interval: [p.Any],
        });
        this.internal({
            plots: [p.Array, []],
        });
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.change, () => this._emit_callback());
    }
    _emit_callback() {
        if (this.callback != null) {
            if (types_1.isFunction(this.callback))
                this.callback(this);
            else
                this.callback.execute(this, {});
        }
    }
    get is_reversed() {
        return this.start > this.end;
    }
}
exports.Range = Range;
Range.__name__ = "Range";
Range.init_Range();
