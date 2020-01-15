"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transform_1 = require("./transform");
const p = require("../../core/properties");
const object_1 = require("../../core/util/object");
const string_1 = require("../../core/util/string");
class CustomJSTransform extends transform_1.Transform {
    constructor(attrs) {
        super(attrs);
    }
    static init_CustomJSTransform() {
        this.define({
            args: [p.Any, {}],
            func: [p.String, ""],
            v_func: [p.String, ""],
            use_strict: [p.Boolean, false],
        });
    }
    get names() {
        return object_1.keys(this.args);
    }
    get values() {
        return object_1.values(this.args);
    }
    _make_transform(name, func) {
        const code = this.use_strict ? string_1.use_strict(func) : func;
        return new Function(...this.names, name, "require", "exports", code);
    }
    get scalar_transform() {
        return this._make_transform("x", this.func);
    }
    get vector_transform() {
        return this._make_transform("xs", this.v_func);
    }
    compute(x) {
        return this.scalar_transform(...this.values, x, require, {});
    }
    v_compute(xs) {
        return this.vector_transform(...this.values, xs, require, {});
    }
}
exports.CustomJSTransform = CustomJSTransform;
CustomJSTransform.__name__ = "CustomJSTransform";
CustomJSTransform.init_CustomJSTransform();
