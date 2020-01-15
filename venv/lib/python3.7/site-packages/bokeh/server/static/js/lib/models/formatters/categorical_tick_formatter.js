"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tick_formatter_1 = require("./tick_formatter");
const array_1 = require("../../core/util/array");
class CategoricalTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    doFormat(ticks, _opts) {
        return array_1.copy(ticks);
    }
}
exports.CategoricalTickFormatter = CategoricalTickFormatter;
CategoricalTickFormatter.__name__ = "CategoricalTickFormatter";
