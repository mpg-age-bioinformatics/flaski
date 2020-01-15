"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const axis_1 = require("./axis");
const linear_axis_1 = require("./linear_axis");
const mercator_tick_formatter_1 = require("../formatters/mercator_tick_formatter");
const mercator_ticker_1 = require("../tickers/mercator_ticker");
class MercatorAxisView extends axis_1.AxisView {
}
exports.MercatorAxisView = MercatorAxisView;
MercatorAxisView.__name__ = "MercatorAxisView";
class MercatorAxis extends linear_axis_1.LinearAxis {
    constructor(attrs) {
        super(attrs);
    }
    static init_MercatorAxis() {
        this.prototype.default_view = MercatorAxisView;
        this.override({
            ticker: () => new mercator_ticker_1.MercatorTicker({ dimension: "lat" }),
            formatter: () => new mercator_tick_formatter_1.MercatorTickFormatter({ dimension: "lat" }),
        });
    }
}
exports.MercatorAxis = MercatorAxis;
MercatorAxis.__name__ = "MercatorAxis";
MercatorAxis.init_MercatorAxis();
