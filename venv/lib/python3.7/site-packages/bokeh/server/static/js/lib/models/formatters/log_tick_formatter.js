"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tick_formatter_1 = require("./tick_formatter");
const basic_tick_formatter_1 = require("./basic_tick_formatter");
const logging_1 = require("../../core/logging");
const p = require("../../core/properties");
class LogTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_LogTickFormatter() {
        this.define({
            ticker: [p.Instance, null],
        });
    }
    initialize() {
        super.initialize();
        this.basic_formatter = new basic_tick_formatter_1.BasicTickFormatter();
        if (this.ticker == null)
            logging_1.logger.warn("LogTickFormatter not configured with a ticker, using default base of 10 (labels will be incorrect if ticker base is not 10)");
    }
    doFormat(ticks, opts) {
        if (ticks.length == 0)
            return [];
        const base = this.ticker != null ? this.ticker.base : 10;
        let small_interval = false;
        const labels = new Array(ticks.length);
        for (let i = 0, end = ticks.length; i < end; i++) {
            labels[i] = `${base}^${Math.round(Math.log(ticks[i]) / Math.log(base))}`;
            if (i > 0 && labels[i] == labels[i - 1]) {
                small_interval = true;
                break;
            }
        }
        if (small_interval)
            return this.basic_formatter.doFormat(ticks, opts);
        else
            return labels;
    }
}
exports.LogTickFormatter = LogTickFormatter;
LogTickFormatter.__name__ = "LogTickFormatter";
LogTickFormatter.init_LogTickFormatter();
