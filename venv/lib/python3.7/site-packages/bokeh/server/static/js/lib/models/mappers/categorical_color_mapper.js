"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const categorical_mapper_1 = require("./categorical_mapper");
const color_mapper_1 = require("./color_mapper");
const p = require("../../core/properties");
class CategoricalColorMapper extends color_mapper_1.ColorMapper {
    constructor(attrs) {
        super(attrs);
    }
    static init_CategoricalColorMapper() {
        this.define({
            factors: [p.Array],
            start: [p.Number, 0],
            end: [p.Number],
        });
    }
    _v_compute(data, values, palette, { nan_color }) {
        categorical_mapper_1.cat_v_compute(data, this.factors, palette, values, this.start, this.end, nan_color);
    }
}
exports.CategoricalColorMapper = CategoricalColorMapper;
CategoricalColorMapper.__name__ = "CategoricalColorMapper";
CategoricalColorMapper.init_CategoricalColorMapper();
