"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const array_1 = require("./array");
const eq_1 = require("./eq");
const types_1 = require("./types");
class MultiDict {
    constructor() {
        this._dict = {};
    }
    _existing(key) {
        if (key in this._dict)
            return this._dict[key];
        else
            return null;
    }
    add_value(key, value) {
        /*
        if value == null
          throw new Error("Can't put null in this dict")
        if isArray(value)
          throw new Error("Can't put arrays in this dict")
        */
        const existing = this._existing(key);
        if (existing == null) {
            this._dict[key] = value;
        }
        else if (types_1.isArray(existing)) {
            existing.push(value);
        }
        else {
            this._dict[key] = [existing, value];
        }
    }
    remove_value(key, value) {
        const existing = this._existing(key);
        if (types_1.isArray(existing)) {
            const new_array = array_1.difference(existing, [value]);
            if (new_array.length > 0)
                this._dict[key] = new_array;
            else
                delete this._dict[key];
        }
        else if (eq_1.isEqual(existing, value)) {
            delete this._dict[key];
        }
    }
    get_one(key, duplicate_error) {
        const existing = this._existing(key);
        if (types_1.isArray(existing)) {
            if (existing.length === 1)
                return existing[0];
            else
                throw new Error(duplicate_error);
        }
        else
            return existing;
    }
}
exports.MultiDict = MultiDict;
MultiDict.__name__ = "MultiDict";
class Set {
    constructor(obj) {
        if (obj == null)
            this._values = [];
        else if (obj instanceof Set)
            this._values = array_1.copy(obj._values);
        else {
            this._values = [];
            for (const item of obj)
                this.add(item);
        }
    }
    get values() {
        return array_1.copy(this._values).sort();
    }
    toString() {
        return `Set([${this.values.join(",")}])`;
    }
    get size() {
        return this._values.length;
    }
    has(item) {
        return this._values.indexOf(item) !== -1;
    }
    add(item) {
        if (!this.has(item))
            this._values.push(item);
    }
    remove(item) {
        const i = this._values.indexOf(item);
        if (i !== -1)
            this._values.splice(i, 1);
    }
    toggle(item) {
        const i = this._values.indexOf(item);
        if (i === -1)
            this._values.push(item);
        else
            this._values.splice(i, 1);
    }
    clear() {
        this._values = [];
    }
    union(input) {
        input = new Set(input);
        return new Set(this._values.concat(input._values));
    }
    intersect(input) {
        input = new Set(input);
        const output = new Set();
        for (const item of input._values) {
            if (this.has(item) && input.has(item))
                output.add(item);
        }
        return output;
    }
    diff(input) {
        input = new Set(input);
        const output = new Set();
        for (const item of this._values) {
            if (!input.has(item))
                output.add(item);
        }
        return output;
    }
    forEach(fn, thisArg) {
        for (const value of this._values) {
            fn.call(thisArg || this, value, value, this);
        }
    }
}
exports.Set = Set;
Set.__name__ = "Set";
class Matrix {
    constructor(nrows, ncols, init) {
        this.nrows = nrows;
        this.ncols = ncols;
        this._matrix = new Array(nrows);
        for (let y = 0; y < nrows; y++) {
            this._matrix[y] = new Array(ncols);
            for (let x = 0; x < ncols; x++) {
                this._matrix[y][x] = init(y, x);
            }
        }
    }
    at(row, col) {
        return this._matrix[row][col];
    }
    map(fn) {
        return new Matrix(this.nrows, this.ncols, (row, col) => fn(this.at(row, col), row, col));
    }
    apply(obj) {
        const fn = Matrix.from(obj);
        const { nrows, ncols } = this;
        if (nrows == fn.nrows && ncols == fn.ncols)
            return new Matrix(nrows, ncols, (row, col) => fn.at(row, col)(this.at(row, col), row, col));
        else
            throw new Error("dimensions don't match");
    }
    to_sparse() {
        const items = [];
        for (let y = 0; y < this.nrows; y++) {
            for (let x = 0; x < this.ncols; x++) {
                const value = this._matrix[y][x];
                items.push([value, y, x]);
            }
        }
        return items;
    }
    static from(obj) {
        if (obj instanceof Matrix)
            return obj;
        else {
            const nrows = obj.length;
            const ncols = array_1.min(obj.map((row) => row.length));
            return new Matrix(nrows, ncols, (row, col) => obj[row][col]);
        }
    }
}
exports.Matrix = Matrix;
Matrix.__name__ = "Matrix";
