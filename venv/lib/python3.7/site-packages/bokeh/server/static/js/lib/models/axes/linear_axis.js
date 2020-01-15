"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axis_1 = require("./axis");
const continuous_axis_1 = require("./continuous_axis");
const basic_tick_formatter_1 = require("../formatters/basic_tick_formatter");
const basic_ticker_1 = require("../tickers/basic_ticker");
class LinearAxisView extends axis_1.AxisView {
}
exports.LinearAxisView = LinearAxisView;
LinearAxisView.__name__ = "LinearAxisView";
class LinearAxis extends continuous_axis_1.ContinuousAxis {
    constructor(attrs) {
        super(attrs);
    }
    static init_LinearAxis() {
        this.prototype.default_view = LinearAxisView;
        this.override({
            ticker: () => new basic_ticker_1.BasicTicker(),
            formatter: () => new basic_tick_formatter_1.BasicTickFormatter(),
        });
    }
}
exports.LinearAxis = LinearAxis;
LinearAxis.__name__ = "LinearAxis";
LinearAxis.init_LinearAxis();
