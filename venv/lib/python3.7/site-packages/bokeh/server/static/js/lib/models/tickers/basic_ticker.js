"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const adaptive_ticker_1 = require("./adaptive_ticker");
class BasicTicker extends adaptive_ticker_1.AdaptiveTicker {
    constructor(attrs) {
        super(attrs);
    }
}
exports.BasicTicker = BasicTicker;
BasicTicker.__name__ = "BasicTicker";
