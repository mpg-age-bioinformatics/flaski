"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const array_1 = require("../../core/util/array");
const adaptive_ticker_1 = require("./adaptive_ticker");
const composite_ticker_1 = require("./composite_ticker");
const days_ticker_1 = require("./days_ticker");
const months_ticker_1 = require("./months_ticker");
const years_ticker_1 = require("./years_ticker");
const util_1 = require("./util");
class DatetimeTicker extends composite_ticker_1.CompositeTicker {
    constructor(attrs) {
        super(attrs);
    }
    static init_DatetimeTicker() {
        this.override({
            num_minor_ticks: 0,
            tickers: () => [
                // Sub-second.
                new adaptive_ticker_1.AdaptiveTicker({
                    mantissas: [1, 2, 5],
                    base: 10,
                    min_interval: 0,
                    max_interval: 500 * util_1.ONE_MILLI,
                    num_minor_ticks: 0,
                }),
                // Seconds, minutes.
                new adaptive_ticker_1.AdaptiveTicker({
                    mantissas: [1, 2, 5, 10, 15, 20, 30],
                    base: 60,
                    min_interval: util_1.ONE_SECOND,
                    max_interval: 30 * util_1.ONE_MINUTE,
                    num_minor_ticks: 0,
                }),
                // Hours.
                new adaptive_ticker_1.AdaptiveTicker({
                    mantissas: [1, 2, 4, 6, 8, 12],
                    base: 24.0,
                    min_interval: util_1.ONE_HOUR,
                    max_interval: 12 * util_1.ONE_HOUR,
                    num_minor_ticks: 0,
                }),
                // Days.
                new days_ticker_1.DaysTicker({ days: array_1.range(1, 32) }),
                new days_ticker_1.DaysTicker({ days: array_1.range(1, 31, 3) }),
                new days_ticker_1.DaysTicker({ days: [1, 8, 15, 22] }),
                new days_ticker_1.DaysTicker({ days: [1, 15] }),
                // Months.
                new months_ticker_1.MonthsTicker({ months: array_1.range(0, 12, 1) }),
                new months_ticker_1.MonthsTicker({ months: array_1.range(0, 12, 2) }),
                new months_ticker_1.MonthsTicker({ months: array_1.range(0, 12, 4) }),
                new months_ticker_1.MonthsTicker({ months: array_1.range(0, 12, 6) }),
                // Years
                new years_ticker_1.YearsTicker({}),
            ],
        });
    }
}
exports.DatetimeTicker = DatetimeTicker;
DatetimeTicker.__name__ = "DatetimeTicker";
DatetimeTicker.init_DatetimeTicker();
