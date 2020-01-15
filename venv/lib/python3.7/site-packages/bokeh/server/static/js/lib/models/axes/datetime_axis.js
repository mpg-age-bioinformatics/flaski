"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const linear_axis_1 = require("./linear_axis");
const datetime_tick_formatter_1 = require("../formatters/datetime_tick_formatter");
const datetime_ticker_1 = require("../tickers/datetime_ticker");
class DatetimeAxisView extends linear_axis_1.LinearAxisView {
}
exports.DatetimeAxisView = DatetimeAxisView;
DatetimeAxisView.__name__ = "DatetimeAxisView";
class DatetimeAxis extends linear_axis_1.LinearAxis {
    constructor(attrs) {
        super(attrs);
    }
    static init_DatetimeAxis() {
        this.prototype.default_view = DatetimeAxisView;
        this.override({
            ticker: () => new datetime_ticker_1.DatetimeTicker(),
            formatter: () => new datetime_tick_formatter_1.DatetimeTickFormatter(),
        });
    }
}
exports.DatetimeAxis = DatetimeAxis;
DatetimeAxis.__name__ = "DatetimeAxis";
DatetimeAxis.init_DatetimeAxis();
