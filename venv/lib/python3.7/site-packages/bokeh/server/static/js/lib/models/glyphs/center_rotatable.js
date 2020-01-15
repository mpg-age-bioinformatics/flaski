"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const p = require("../../core/properties");
class CenterRotatableView extends xy_glyph_1.XYGlyphView {
}
exports.CenterRotatableView = CenterRotatableView;
CenterRotatableView.__name__ = "CenterRotatableView";
class CenterRotatable extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_CenterRotatable() {
        this.mixins(['line', 'fill']);
        this.define({
            angle: [p.AngleSpec, 0],
            width: [p.DistanceSpec],
            height: [p.DistanceSpec],
        });
    }
}
exports.CenterRotatable = CenterRotatable;
CenterRotatable.__name__ = "CenterRotatable";
CenterRotatable.init_CenterRotatable();
