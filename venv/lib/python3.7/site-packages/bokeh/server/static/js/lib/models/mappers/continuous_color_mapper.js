"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const color_mapper_1 = require("./color_mapper");
const p = require("../../core/properties");
class ContinuousColorMapper extends color_mapper_1.ColorMapper {
    constructor(attrs) {
        super(attrs);
    }
    static init_ContinuousColorMapper() {
        this.define({
            high: [p.Number],
            low: [p.Number],
            high_color: [p.Color],
            low_color: [p.Color],
        });
    }
    _colors(conv) {
        return Object.assign(Object.assign({}, super._colors(conv)), { low_color: this.low_color != null ? conv(this.low_color) : undefined, high_color: this.high_color != null ? conv(this.high_color) : undefined });
    }
}
exports.ContinuousColorMapper = ContinuousColorMapper;
ContinuousColorMapper.__name__ = "ContinuousColorMapper";
ContinuousColorMapper.init_ContinuousColorMapper();
