"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const categorical_mapper_1 = require("./categorical_mapper");
const mapper_1 = require("./mapper");
const p = require("../../core/properties");
class CategoricalMarkerMapper extends mapper_1.Mapper {
    constructor(attrs) {
        super(attrs);
    }
    static init_CategoricalMarkerMapper() {
        this.define({
            factors: [p.Array],
            markers: [p.Array],
            start: [p.Number, 0],
            end: [p.Number],
            default_value: [p.MarkerType, "circle"],
        });
    }
    v_compute(xs) {
        const values = new Array(xs.length);
        categorical_mapper_1.cat_v_compute(xs, this.factors, this.markers, values, this.start, this.end, this.default_value);
        return values;
    }
}
exports.CategoricalMarkerMapper = CategoricalMarkerMapper;
CategoricalMarkerMapper.__name__ = "CategoricalMarkerMapper";
CategoricalMarkerMapper.init_CategoricalMarkerMapper();
