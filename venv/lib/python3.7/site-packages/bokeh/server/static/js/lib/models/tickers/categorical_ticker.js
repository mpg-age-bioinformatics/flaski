"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const ticker_1 = require("./ticker");
class CategoricalTicker extends ticker_1.Ticker {
    constructor(attrs) {
        super(attrs);
    }
    get_ticks(start, end, range, _cross_loc, _) {
        const majors = this._collect(range.factors, range, start, end);
        const tops = this._collect(range.tops || [], range, start, end);
        const mids = this._collect(range.mids || [], range, start, end);
        return {
            major: majors,
            minor: [],
            tops,
            mids,
        };
    }
    _collect(factors, range, start, end) {
        const result = [];
        for (const factor of factors) {
            const coord = range.synthetic(factor);
            if (coord > start && coord < end)
                result.push(factor);
        }
        return result;
    }
}
exports.CategoricalTicker = CategoricalTicker;
CategoricalTicker.__name__ = "CategoricalTicker";
