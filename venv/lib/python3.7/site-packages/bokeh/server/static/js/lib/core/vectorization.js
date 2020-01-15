"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const types_1 = require("./util/types");
function isValue(obj) {
    return types_1.isPlainObject(obj) && "value" in obj;
}
exports.isValue = isValue;
function isField(obj) {
    return types_1.isPlainObject(obj) && "field" in obj;
}
exports.isField = isField;
