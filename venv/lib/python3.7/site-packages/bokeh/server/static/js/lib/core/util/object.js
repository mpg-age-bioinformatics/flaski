"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const tslib_1 = require("tslib");
const array_1 = require("./array");
exports.keys = Object.keys;
function values(object) {
    const keys = Object.keys(object);
    const length = keys.length;
    const values = new Array(length);
    for (let i = 0; i < length; i++) {
        values[i] = object[keys[i]];
    }
    return values;
}
exports.values = values;
function extend(dest, src) {
    return tslib_1.__assign(dest, src);
}
exports.extend = extend;
function clone(obj) {
    return extend({}, obj); // XXX: can't use {...obj} due to https://github.com/Microsoft/TypeScript/issues/14409
}
exports.clone = clone;
function merge(obj1, obj2) {
    /*
     * Returns an object with the array values for obj1 and obj2 unioned by key.
     */
    const result = Object.create(Object.prototype);
    const keys = array_1.concat([Object.keys(obj1), Object.keys(obj2)]);
    for (const key of keys) {
        const arr1 = obj1.hasOwnProperty(key) ? obj1[key] : [];
        const arr2 = obj2.hasOwnProperty(key) ? obj2[key] : [];
        result[key] = array_1.union(arr1, arr2);
    }
    return result;
}
exports.merge = merge;
function size(obj) {
    return Object.keys(obj).length;
}
exports.size = size;
function isEmpty(obj) {
    return size(obj) === 0;
}
exports.isEmpty = isEmpty;
