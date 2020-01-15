"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const continuous_ticker_1 = require("./continuous_ticker");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
const object_1 = require("../../core/util/object");
class CompositeTicker extends continuous_ticker_1.ContinuousTicker {
    constructor(attrs) {
        super(attrs);
    }
    static init_CompositeTicker() {
        this.define({
            tickers: [p.Array, []],
        });
    }
    // The tickers should be in order of increasing interval size; specifically,
    // if S comes before T, then it should be the case that
    // S.get_max_interval() < T.get_min_interval().
    // FIXME Enforce this automatically.
    get min_intervals() {
        return this.tickers.map((ticker) => ticker.get_min_interval());
    }
    get max_intervals() {
        return this.tickers.map((ticker) => ticker.get_max_interval());
    }
    get min_interval() {
        return this.min_intervals[0];
    }
    get max_interval() {
        return this.max_intervals[0];
    }
    get_best_ticker(data_low, data_high, desired_n_ticks) {
        const data_range = data_high - data_low;
        const ideal_interval = this.get_ideal_interval(data_low, data_high, desired_n_ticks);
        const ticker_ndxs = [
            array_1.sorted_index(this.min_intervals, ideal_interval) - 1,
            array_1.sorted_index(this.max_intervals, ideal_interval),
        ];
        const intervals = [
            this.min_intervals[ticker_ndxs[0]],
            this.max_intervals[ticker_ndxs[1]],
        ];
        const errors = intervals.map((interval) => {
            return Math.abs(desired_n_ticks - (data_range / interval));
        });
        let best_ticker;
        if (object_1.isEmpty(errors.filter((e) => !isNaN(e)))) {
            // this can happen if the data isn't loaded yet, we just default to the first scale
            best_ticker = this.tickers[0];
        }
        else {
            const best_index = array_1.argmin(errors);
            const best_ticker_ndx = ticker_ndxs[best_index];
            best_ticker = this.tickers[best_ticker_ndx];
        }
        return best_ticker;
    }
    get_interval(data_low, data_high, desired_n_ticks) {
        const best_ticker = this.get_best_ticker(data_low, data_high, desired_n_ticks);
        return best_ticker.get_interval(data_low, data_high, desired_n_ticks);
    }
    get_ticks_no_defaults(data_low, data_high, cross_loc, desired_n_ticks) {
        const best_ticker = this.get_best_ticker(data_low, data_high, desired_n_ticks);
        return best_ticker.get_ticks_no_defaults(data_low, data_high, cross_loc, desired_n_ticks);
    }
}
exports.CompositeTicker = CompositeTicker;
CompositeTicker.__name__ = "CompositeTicker";
CompositeTicker.init_CompositeTicker();
