"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const expression_1 = require("./expression");
const p = require("../../core/properties");
class Stack extends expression_1.Expression {
    constructor(attrs) {
        super(attrs);
    }
    static init_Stack() {
        this.define({
            fields: [p.Array, []],
        });
    }
    _v_compute(source) {
        const n = source.get_length() || 0; // TODO: use ?? in TS 3.7
        const result = new Float64Array(n);
        for (const f of this.fields) {
            const column = source.data[f];
            if (column != null) {
                for (let i = 0, k = Math.min(n, column.length); i < k; i++) {
                    result[i] += column[i];
                }
            }
        }
        return result;
    }
}
exports.Stack = Stack;
Stack.__name__ = "Stack";
Stack.init_Stack();
