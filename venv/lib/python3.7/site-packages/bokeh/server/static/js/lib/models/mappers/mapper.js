"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const transform_1 = require("../transforms/transform");
class Mapper extends transform_1.Transform {
    constructor(attrs) {
        super(attrs);
    }
    compute(_x) {
        // If it's just a single value, then a mapper doesn't really make sense.
        throw new Error("mapping single values is not supported");
    }
}
exports.Mapper = Mapper;
Mapper.__name__ = "Mapper";
