"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tick_formatter_1 = require("./tick_formatter");
const templating_1 = require("../../core/util/templating");
const p = require("../../core/properties");
class PrintfTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_PrintfTickFormatter() {
        this.define({
            format: [p.String, '%s'],
        });
    }
    doFormat(ticks, _opts) {
        return ticks.map((tick) => templating_1.sprintf(this.format, tick));
    }
}
exports.PrintfTickFormatter = PrintfTickFormatter;
PrintfTickFormatter.__name__ = "PrintfTickFormatter";
PrintfTickFormatter.init_PrintfTickFormatter();
