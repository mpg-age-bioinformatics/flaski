"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
class Expression extends model_1.Model {
    constructor(attrs) {
        super(attrs);
        this._connected = {};
        this._result = {};
    }
    initialize() {
        super.initialize();
        this._connected = {};
        this._result = {};
    }
    v_compute(source) {
        if (this._connected[source.id] == null) {
            this.connect(source.change, () => delete this._result[source.id]);
            this.connect(source.patching, () => delete this._result[source.id]);
            this.connect(source.streaming, () => delete this._result[source.id]);
            this._connected[source.id] = true;
        }
        let result = this._result[source.id];
        if (result == null)
            this._result[source.id] = result = this._v_compute(source);
        return result;
    }
}
exports.Expression = Expression;
Expression.__name__ = "Expression";
