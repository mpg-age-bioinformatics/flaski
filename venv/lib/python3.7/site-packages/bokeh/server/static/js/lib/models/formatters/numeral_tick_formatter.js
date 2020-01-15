"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const Numbro = require("numbro");
const tick_formatter_1 = require("./tick_formatter");
const p = require("../../core/properties");
class NumeralTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_NumeralTickFormatter() {
        this.define({
            // TODO (bev) all of these could be tightened up
            format: [p.String, '0,0'],
            language: [p.String, 'en'],
            rounding: [p.RoundingFunction, 'round'],
        });
    }
    get _rounding_fn() {
        switch (this.rounding) {
            case "round":
            case "nearest":
                return Math.round;
            case "floor":
            case "rounddown":
                return Math.floor;
            case "ceil":
            case "roundup":
                return Math.ceil;
        }
    }
    doFormat(ticks, _opts) {
        const { format, language, _rounding_fn } = this;
        return ticks.map((tick) => Numbro.format(tick, format, language, _rounding_fn));
    }
}
exports.NumeralTickFormatter = NumeralTickFormatter;
NumeralTickFormatter.__name__ = "NumeralTickFormatter";
NumeralTickFormatter.init_NumeralTickFormatter();
