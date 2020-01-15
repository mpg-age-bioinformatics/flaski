"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const continuous_ticker_1 = require("./continuous_ticker");
const p = require("../../core/properties");
class FixedTicker extends continuous_ticker_1.ContinuousTicker {
    constructor(attrs) {
        super(attrs);
        this.min_interval = 0;
        this.max_interval = 0;
    }
    static init_FixedTicker() {
        this.define({
            ticks: [p.Array, []],
            minor_ticks: [p.Array, []],
        });
    }
    get_ticks_no_defaults(_data_low, _data_high, _cross_loc, _desired_n_ticks) {
        return {
            major: this.ticks,
            minor: this.minor_ticks,
        };
    }
    // XXX: whatever, because FixedTicker needs to fulfill the interface somehow
    get_interval(_data_low, _data_high, _desired_n_ticks) {
        return 0;
    }
}
exports.FixedTicker = FixedTicker;
FixedTicker.__name__ = "FixedTicker";
FixedTicker.init_FixedTicker();
