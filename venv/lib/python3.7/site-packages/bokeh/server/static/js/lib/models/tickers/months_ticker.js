"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const single_interval_ticker_1 = require("./single_interval_ticker");
const util_1 = require("./util");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
// Given a start and end time in millis, returns the shortest array of
// consecutive years (as Dates) that surrounds both times.
function date_range_by_year(start_time, end_time) {
    const start_date = util_1.last_year_no_later_than(new Date(start_time));
    const end_date = util_1.last_year_no_later_than(new Date(end_time));
    end_date.setUTCFullYear(end_date.getUTCFullYear() + 1);
    const dates = [];
    const date = start_date;
    while (true) {
        dates.push(util_1.copy_date(date));
        date.setUTCFullYear(date.getUTCFullYear() + 1);
        if (date > end_date)
            break;
    }
    return dates;
}
class MonthsTicker extends single_interval_ticker_1.SingleIntervalTicker {
    constructor(attrs) {
        super(attrs);
    }
    static init_MonthsTicker() {
        this.define({
            months: [p.Array, []],
        });
    }
    initialize() {
        super.initialize();
        const months = this.months;
        if (months.length > 1)
            this.interval = (months[1] - months[0]) * util_1.ONE_MONTH;
        else
            this.interval = 12 * util_1.ONE_MONTH;
    }
    get_ticks_no_defaults(data_low, data_high, _cross_loc, _desired_n_ticks) {
        const year_dates = date_range_by_year(data_low, data_high);
        const months = this.months;
        const months_of_year = (year_date) => {
            return months.map((month) => {
                const month_date = util_1.copy_date(year_date);
                month_date.setUTCMonth(month);
                return month_date;
            });
        };
        const month_dates = array_1.concat(year_dates.map(months_of_year));
        const all_ticks = month_dates.map((month_date) => month_date.getTime());
        const ticks_in_range = all_ticks.filter((tick) => data_low <= tick && tick <= data_high);
        return {
            major: ticks_in_range,
            minor: [],
        };
    }
}
exports.MonthsTicker = MonthsTicker;
MonthsTicker.__name__ = "MonthsTicker";
MonthsTicker.init_MonthsTicker();
