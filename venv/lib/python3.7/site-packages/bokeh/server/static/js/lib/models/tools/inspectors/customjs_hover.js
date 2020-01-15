"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../../model");
const p = require("../../../core/properties");
const object_1 = require("../../../core/util/object");
const string_1 = require("../../../core/util/string");
class CustomJSHover extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_CustomJSHover() {
        this.define({
            args: [p.Any, {}],
            code: [p.String, ""],
        });
    }
    get values() {
        return object_1.values(this.args);
    }
    /*protected*/ _make_code(valname, formatname, varsname, fn) {
        // this relies on keys(args) and values(args) returning keys and values
        // in the same order
        return new Function(...object_1.keys(this.args), valname, formatname, varsname, "require", "exports", string_1.use_strict(fn));
    }
    format(value, format, special_vars) {
        const formatter = this._make_code("value", "format", "special_vars", this.code);
        return formatter(...this.values, value, format, special_vars, require, exports);
    }
}
exports.CustomJSHover = CustomJSHover;
CustomJSHover.__name__ = "CustomJSHover";
CustomJSHover.init_CustomJSHover();
