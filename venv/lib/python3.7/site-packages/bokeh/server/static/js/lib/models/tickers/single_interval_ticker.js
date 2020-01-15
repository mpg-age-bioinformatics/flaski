"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const continuous_ticker_1 = require("./continuous_ticker");
const p = require("../../core/properties");
class SingleIntervalTicker extends continuous_ticker_1.ContinuousTicker {
    constructor(attrs) {
        super(attrs);
    }
    static init_SingleIntervalTicker() {
        this.define({
            interval: [p.Number],
        });
    }
    get_interval(_data_low, _data_high, _n_desired_ticks) {
        return this.interval;
    }
    get min_interval() {
        return this.interval;
    }
    get max_interval() {
        return this.interval;
    }
}
exports.SingleIntervalTicker = SingleIntervalTicker;
SingleIntervalTicker.__name__ = "SingleIntervalTicker";
SingleIntervalTicker.init_SingleIntervalTicker();
