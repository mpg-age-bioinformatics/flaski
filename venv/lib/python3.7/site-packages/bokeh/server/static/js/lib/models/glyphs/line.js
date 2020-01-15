"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const utils_1 = require("./utils");
const hittest = require("../../core/hittest");
class LineView extends xy_glyph_1.XYGlyphView {
    _render(ctx, indices, { sx, sy }) {
        let drawing = false;
        let last_index = null;
        this.visuals.line.set_value(ctx);
        for (const i of indices) {
            if (drawing) {
                if (!isFinite(sx[i] + sy[i])) {
                    ctx.stroke();
                    ctx.beginPath();
                    drawing = false;
                    last_index = i;
                    continue;
                }
                if (last_index != null && i - last_index > 1) {
                    ctx.stroke();
                    drawing = false;
                }
            }
            if (drawing)
                ctx.lineTo(sx[i], sy[i]);
            else {
                ctx.beginPath();
                ctx.moveTo(sx[i], sy[i]);
                drawing = true;
            }
            last_index = i;
        }
        if (drawing)
            ctx.stroke();
    }
    _hit_point(geometry) {
        /* Check if the point geometry hits this line glyph and return an object
        that describes the hit result:
          Args:
            * geometry (object): object with the following keys
              * sx (float): screen x coordinate of the point
              * sy (float): screen y coordinate of the point
              * type (str): type of geometry (in this case it's a point)
          Output:
            Object with the following keys:
              * 0d (bool): whether the point hits the glyph or not
              * 1d (array(int)): array with the indices hit by the point
        */
        const result = hittest.create_empty_hit_test_result();
        const point = { x: geometry.sx, y: geometry.sy };
        let shortest = 9999;
        const threshold = Math.max(2, this.visuals.line.line_width.value() / 2);
        for (let i = 0, end = this.sx.length - 1; i < end; i++) {
            const p0 = { x: this.sx[i], y: this.sy[i] };
            const p1 = { x: this.sx[i + 1], y: this.sy[i + 1] };
            const dist = hittest.dist_to_segment(point, p0, p1);
            if (dist < threshold && dist < shortest) {
                shortest = dist;
                result.add_to_selected_glyphs(this.model);
                result.get_view = () => this;
                result.line_indices = [i];
            }
        }
        return result;
    }
    _hit_span(geometry) {
        const { sx, sy } = geometry;
        const result = hittest.create_empty_hit_test_result();
        let val;
        let values;
        if (geometry.direction == 'v') {
            val = this.renderer.yscale.invert(sy);
            values = this._y;
        }
        else {
            val = this.renderer.xscale.invert(sx);
            values = this._x;
        }
        for (let i = 0, end = values.length - 1; i < end; i++) {
            if ((values[i] <= val && val <= values[i + 1]) || (values[i + 1] <= val && val <= values[i])) {
                result.add_to_selected_glyphs(this.model);
                result.get_view = () => this;
                result.line_indices.push(i);
            }
        }
        return result;
    }
    get_interpolation_hit(i, geometry) {
        const [x2, y2, x3, y3] = [this._x[i], this._y[i], this._x[i + 1], this._y[i + 1]];
        return utils_1.line_interpolation(this.renderer, geometry, x2, y2, x3, y3);
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_line_legend(this.visuals, ctx, bbox, index);
    }
}
exports.LineView = LineView;
LineView.__name__ = "LineView";
class Line extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Line() {
        this.prototype.default_view = LineView;
        this.mixins(['line']);
    }
}
exports.Line = Line;
Line.__name__ = "Line";
Line.init_Line();
