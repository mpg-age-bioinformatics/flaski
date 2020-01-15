"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const callback_1 = require("./callback");
const p = require("../../core/properties");
const object_1 = require("../../core/util/object");
const string_1 = require("../../core/util/string");
class CustomJS extends callback_1.Callback {
    constructor(attrs) {
        super(attrs);
    }
    static init_CustomJS() {
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
        return new Function(...this.names, "cb_obj", "cb_data", "require", "exports", code);
    }
    execute(cb_obj, cb_data = {}) {
        return this.func.apply(cb_obj, this.values.concat(cb_obj, cb_data, require, {}));
    }
}
exports.CustomJS = CustomJS;
CustomJS.__name__ = "CustomJS";
CustomJS.init_CustomJS();
