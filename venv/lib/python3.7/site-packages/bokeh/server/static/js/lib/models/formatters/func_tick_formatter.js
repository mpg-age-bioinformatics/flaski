"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tick_formatter_1 = require("./tick_formatter");
const p = require("../../core/properties");
const object_1 = require("../../core/util/object");
const string_1 = require("../../core/util/string");
class FuncTickFormatter extends tick_formatter_1.TickFormatter {
    constructor(attrs) {
        super(attrs);
    }
    static init_FuncTickFormatter() {
        this.define({
            args: [p.Any, {}],
            code: [p.String, ''],
            use_strict: [p.Boolean, false],
        });
    }
    get names() {
        return object_1.keys(this.args);
    }
    get values() {
        return object_1.values(this.args);
    }
    /*protected*/ _make_func() {
        const code = this.use_strict ? string_1.use_strict(this.code) : this.code;
        return new Function("tick", "index", "ticks", ...this.names, "require", "exports", code);
    }
    doFormat(ticks, _opts) {
        const cache = {};
        const func = this._make_func().bind(cache);
        return ticks.map((tick, index, ticks) => func(tick, index, ticks, ...this.values, require, {}));
    }
}
exports.FuncTickFormatter = FuncTickFormatter;
FuncTickFormatter.__name__ = "FuncTickFormatter";
FuncTickFormatter.init_FuncTickFormatter();
