"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const spatial_1 = require("../../core/util/spatial");
const glyph_1 = require("./glyph");
class XYGlyphView extends glyph_1.GlyphView {
    _index_data() {
        const points = [];
        for (let i = 0, end = this._x.length; i < end; i++) {
            const x = this._x[i];
            const y = this._y[i];
            if (isNaN(x + y) || !isFinite(x + y))
                continue;
            points.push({ x0: x, y0: y, x1: x, y1: y, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    scenterx(i) {
        return this.sx[i];
    }
    scentery(i) {
        return this.sy[i];
    }
}
exports.XYGlyphView = XYGlyphView;
XYGlyphView.__name__ = "XYGlyphView";
class XYGlyph extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_XYGlyph() {
        this.coords([['x', 'y']]);
    }
}
exports.XYGlyph = XYGlyph;
XYGlyph.__name__ = "XYGlyph";
XYGlyph.init_XYGlyph();
