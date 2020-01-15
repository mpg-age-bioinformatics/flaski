"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
class AreaView extends glyph_1.GlyphView {
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_area_legend(this.visuals, ctx, bbox, index);
    }
}
exports.AreaView = AreaView;
AreaView.__name__ = "AreaView";
class Area extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Area() {
        this.mixins(['fill', 'hatch']);
    }
}
exports.Area = Area;
Area.__name__ = "Area";
Area.init_Area();
