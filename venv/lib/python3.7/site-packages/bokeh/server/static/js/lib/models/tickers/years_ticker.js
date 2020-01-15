"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const basic_ticker_1 = require("./basic_ticker");
const single_interval_ticker_1 = require("./single_interval_ticker");
const util_1 = require("./util");
class YearsTicker extends single_interval_ticker_1.SingleIntervalTicker {
    constructor(attrs) {
        super(attrs);
    }
    initialize() {
        super.initialize();
        this.interval = util_1.ONE_YEAR;
        this.basic_ticker = new basic_ticker_1.BasicTicker({ num_minor_ticks: 0 });
    }
    get_ticks_no_defaults(data_low, data_high, cross_loc, desired_n_ticks) {
        const start_year = util_1.last_year_no_later_than(new Date(data_low)).getUTCFullYear();
        const end_year = util_1.last_year_no_later_than(new Date(data_high)).getUTCFullYear();
        const years = this.basic_ticker.get_ticks_no_defaults(start_year, end_year, cross_loc, desired_n_ticks).major;
        const all_ticks = years.map((year) => Date.UTC(year, 0, 1));
        const ticks_in_range = all_ticks.filter((tick) => data_low <= tick && tick <= data_high);
        return {
            major: ticks_in_range,
            minor: [],
        };
    }
}
exports.YearsTicker = YearsTicker;
YearsTicker.__name__ = "YearsTicker";
