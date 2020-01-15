"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axis_1 = require("./axis");
const continuous_axis_1 = require("./continuous_axis");
const log_tick_formatter_1 = require("../formatters/log_tick_formatter");
const log_ticker_1 = require("../tickers/log_ticker");
class LogAxisView extends axis_1.AxisView {
}
exports.LogAxisView = LogAxisView;
LogAxisView.__name__ = "LogAxisView";
class LogAxis extends continuous_axis_1.ContinuousAxis {
    constructor(attrs) {
        super(attrs);
    }
    static init_LogAxis() {
        this.prototype.default_view = LogAxisView;
        this.override({
            ticker: () => new log_ticker_1.LogTicker(),
            formatter: () => new log_tick_formatter_1.LogTickFormatter(),
        });
    }
}
exports.LogAxis = LogAxis;
LogAxis.__name__ = "LogAxis";
LogAxis.init_LogAxis();
