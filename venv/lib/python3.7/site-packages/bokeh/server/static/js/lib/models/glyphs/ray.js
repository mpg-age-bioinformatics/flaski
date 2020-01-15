"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const utils_1 = require("./utils");
const p = require("../../core/properties");
class RayView extends xy_glyph_1.XYGlyphView {
    _map_data() {
        if (this.model.properties.length.units == "data")
            this.slength = this.sdist(this.renderer.xscale, this._x, this._length);
        else
            this.slength = this._length;
    }
    _render(ctx, indices, { sx, sy, slength, _angle }) {
        if (this.visuals.line.doit) {
            const width = this.renderer.plot_view.frame._width.value;
            const height = this.renderer.plot_view.frame._height.value;
            const inf_len = 2 * (width + height);
            for (let i = 0, end = slength.length; i < end; i++) {
                if (slength[i] == 0)
                    slength[i] = inf_len;
            }
            for (const i of indices) {
                if (isNaN(sx[i] + sy[i] + _angle[i] + slength[i]))
                    continue;
                ctx.translate(sx[i], sy[i]);
                ctx.rotate(_angle[i]);
                ctx.beginPath();
                ctx.moveTo(0, 0);
                ctx.lineTo(slength[i], 0);
                this.visuals.line.set_vectorize(ctx, i);
                ctx.stroke();
                ctx.rotate(-_angle[i]);
                ctx.translate(-sx[i], -sy[i]);
            }
        }
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_line_legend(this.visuals, ctx, bbox, index);
    }
}
exports.RayView = RayView;
RayView.__name__ = "RayView";
class Ray extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Ray() {
        this.prototype.default_view = RayView;
        this.mixins(['line']);
        this.define({
            length: [p.DistanceSpec],
            angle: [p.AngleSpec],
        });
    }
}
exports.Ray = Ray;
Ray.__name__ = "Ray";
Ray.init_Ray();
