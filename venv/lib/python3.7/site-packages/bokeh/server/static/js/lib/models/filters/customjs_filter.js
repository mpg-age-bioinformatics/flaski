"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const filter_1 = require("./filter");
const p = require("../../core/properties");
const object_1 = require("../../core/util/object");
const string_1 = require("../../core/util/string");
class CustomJSFilter extends filter_1.Filter {
    constructor(attrs) {
        super(attrs);
    }
    static init_CustomJSFilter() {
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
    get func() {
        const code = this.use_strict ? string_1.use_strict(this.code) : this.code;
        return new Function(...this.names, "source", "require", "exports", code);
    }
    compute_indices(source) {
        this.filter = this.func(...this.values, source, require, {});
        return super.compute_indices(source);
    }
}
exports.CustomJSFilter = CustomJSFilter;
CustomJSFilter.__name__ = "CustomJSFilter";
CustomJSFilter.init_CustomJSFilter();
