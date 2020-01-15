"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tick_formatter_1 = require("./tick_formatter");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
class BasicTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
        this.last_precision = 3;
    }
    static init_BasicTickFormatter() {
        this.define({
            precision: [p.Any, 'auto'],
            use_scientific: [p.Boolean, true],
            power_limit_high: [p.Number, 5],
            power_limit_low: [p.Number, -3],
        });
    }
    get scientific_limit_low() {
        return Math.pow(10.0, this.power_limit_low);
    }
    get scientific_limit_high() {
        return Math.pow(10.0, this.power_limit_high);
    }
    doFormat(ticks, _opts) {
        if (ticks.length == 0)
            return [];
        let zero_eps = 0;
        if (ticks.length >= 2)
            zero_eps = Math.abs(ticks[1] - ticks[0]) / 10000;
        let need_sci = false;
        if (this.use_scientific) {
            for (const tick of ticks) {
                const tick_abs = Math.abs(tick);
                if (tick_abs > zero_eps && (tick_abs >= this.scientific_limit_high || tick_abs <= this.scientific_limit_low)) {
                    need_sci = true;
                    break;
                }
            }
        }
        const labels = new Array(ticks.length);
        const { precision } = this;
        if (precision == null || types_1.isNumber(precision)) {
            if (need_sci) {
                for (let i = 0, end = ticks.length; i < end; i++) {
                    labels[i] = ticks[i].toExponential(precision || undefined);
                }
            }
            else {
                for (let i = 0, end = ticks.length; i < end; i++) {
                    labels[i] = ticks[i].toFixed(precision || undefined).replace(/(\.[0-9]*?)0+$/, "$1").replace(/\.$/, "");
                }
            }
        }
        else {
            for (let x = this.last_precision, asc = this.last_precision <= 15; asc ? x <= 15 : x >= 15; asc ? x++ : x--) {
                let is_ok = true;
                if (need_sci) {
                    for (let i = 0, end = ticks.length; i < end; i++) {
                        labels[i] = ticks[i].toExponential(x);
                        if (i > 0) {
                            if (labels[i] === labels[i - 1]) {
                                is_ok = false;
                                break;
                            }
                        }
                    }
                    if (is_ok) {
                        break;
                    }
                }
                else {
                    for (let i = 0, end = ticks.length; i < end; i++) {
                        labels[i] = ticks[i].toFixed(x).replace(/(\.[0-9]*?)0+$/, "$1").replace(/\.$/, "");
                        if (i > 0) {
                            if (labels[i] == labels[i - 1]) {
                                is_ok = false;
                                break;
                            }
                        }
                    }
                    if (is_ok) {
                        break;
                    }
                }
                if (is_ok) {
                    this.last_precision = x;
                    break;
                }
            }
        }
        return labels;
    }
}
exports.BasicTickFormatter = BasicTickFormatter;
BasicTickFormatter.__name__ = "BasicTickFormatter";
BasicTickFormatter.init_BasicTickFormatter();
