"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const utils_1 = require("./utils");
const hittest = require("../../core/hittest");
class PatchView extends xy_glyph_1.XYGlyphView {
    _inner_loop(ctx, indices, sx, sy, func) {
        for (const i of indices) {
            if (i == 0) {
                ctx.beginPath();
                ctx.moveTo(sx[i], sy[i]);
                continue;
            }
            else if (isNaN(sx[i] + sy[i])) {
                ctx.closePath();
                func.apply(ctx);
                ctx.beginPath();
                continue;
            }
            else
                ctx.lineTo(sx[i], sy[i]);
        }
        ctx.closePath();
        func.call(ctx);
    }
    _render(ctx, indices, { sx, sy }) {
        if (this.visuals.fill.doit) {
            this.visuals.fill.set_value(ctx);
            this._inner_loop(ctx, indices, sx, sy, ctx.fill);
        }
        this.visuals.hatch.doit2(ctx, 0, () => this._inner_loop(ctx, indices, sx, sy, ctx.fill), () => this.renderer.request_render());
        if (this.visuals.line.doit) {
            this.visuals.line.set_value(ctx);
            this._inner_loop(ctx, indices, sx, sy, ctx.stroke);
        }
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_area_legend(this.visuals, ctx, bbox, index);
    }
    _hit_point(geometry) {
        const result = hittest.create_empty_hit_test_result();
        if (hittest.point_in_poly(geometry.sx, geometry.sy, this.sx, this.sy)) {
            result.add_to_selected_glyphs(this.model);
            result.get_view = () => this;
        }
        return result;
    }
}
exports.PatchView = PatchView;
PatchView.__name__ = "PatchView";
class Patch extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Patch() {
        this.prototype.default_view = PatchView;
        this.mixins(['line', 'fill', 'hatch']);
    }
}
exports.Patch = Patch;
Patch.__name__ = "Patch";
Patch.init_Patch();
