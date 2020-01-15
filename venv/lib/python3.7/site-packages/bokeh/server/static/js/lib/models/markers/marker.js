"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("../glyphs/xy_glyph");
const hittest = require("../../core/hittest");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
class MarkerView extends xy_glyph_1.XYGlyphView {
    _render(ctx, indices, { sx, sy, _size, _angle }) {
        for (const i of indices) {
            if (isNaN(sx[i] + sy[i] + _size[i] + _angle[i]))
                continue;
            const r = _size[i] / 2;
            ctx.beginPath();
            ctx.translate(sx[i], sy[i]);
            if (_angle[i])
                ctx.rotate(_angle[i]);
            this._render_one(ctx, i, r, this.visuals.line, this.visuals.fill);
            if (_angle[i])
                ctx.rotate(-_angle[i]);
            ctx.translate(-sx[i], -sy[i]);
        }
    }
    _mask_data() {
        // dilate the inner screen region by max_size and map back to data space for use in
        // spatial query
        const hr = this.renderer.plot_view.frame.bbox.h_range;
        const sx0 = hr.start - this.max_size;
        const sx1 = hr.end + this.max_size;
        const [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
        const vr = this.renderer.plot_view.frame.bbox.v_range;
        const sy0 = vr.start - this.max_size;
        const sy1 = vr.end + this.max_size;
        const [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        return this.index.indices({ x0, x1, y0, y1 });
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const sx0 = sx - this.max_size;
        const sx1 = sx + this.max_size;
        const [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
        const sy0 = sy - this.max_size;
        const sy1 = sy + this.max_size;
        const [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        const candidates = this.index.indices({ x0, x1, y0, y1 });
        const hits = [];
        for (const i of candidates) {
            const s2 = this._size[i] / 2;
            const dist = Math.abs(this.sx[i] - sx) + Math.abs(this.sy[i] - sy);
            if (Math.abs(this.sx[i] - sx) <= s2 && Math.abs(this.sy[i] - sy) <= s2) {
                hits.push([i, dist]);
            }
        }
        return hittest.create_hit_test_result_from_hits(hits);
    }
    _hit_span(geometry) {
        const { sx, sy } = geometry;
        const bounds = this.bounds();
        const ms = this.max_size / 2;
        const result = hittest.create_empty_hit_test_result();
        let x0, x1, y0, y1;
        if (geometry.direction == 'h') {
            y0 = bounds.y0;
            y1 = bounds.y1;
            const sx0 = sx - ms;
            const sx1 = sx + ms;
            [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
        }
        else {
            x0 = bounds.x0;
            x1 = bounds.x1;
            const sy0 = sy - ms;
            const sy1 = sy + ms;
            [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        }
        const hits = this.index.indices({ x0, x1, y0, y1 });
        result.indices = hits;
        return result;
    }
    _hit_rect(geometry) {
        const { sx0, sx1, sy0, sy1 } = geometry;
        const [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
        const [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        const result = hittest.create_empty_hit_test_result();
        result.indices = this.index.indices({ x0, x1, y0, y1 });
        return result;
    }
    _hit_poly(geometry) {
        const { sx, sy } = geometry;
        // TODO (bev) use spatial index to pare candidate list
        const candidates = array_1.range(0, this.sx.length);
        const hits = [];
        for (let i = 0, end = candidates.length; i < end; i++) {
            const idx = candidates[i];
            if (hittest.point_in_poly(this.sx[i], this.sy[i], sx, sy))
                hits.push(idx);
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    draw_legend_for_index(ctx, { x0, x1, y0, y1 }, index) {
        // using objects like this seems a little wonky, since the keys are coerced to
        // stings, but it works
        const len = index + 1;
        const sx = new Array(len);
        sx[index] = (x0 + x1) / 2;
        const sy = new Array(len);
        sy[index] = (y0 + y1) / 2;
        const size = new Array(len);
        size[index] = Math.min(Math.abs(x1 - x0), Math.abs(y1 - y0)) * 0.4;
        const angle = new Array(len);
        angle[index] = 0; // don't attempt to match glyph angle
        this._render(ctx, [index], { sx, sy, _size: size, _angle: angle }); // XXX
    }
}
exports.MarkerView = MarkerView;
MarkerView.__name__ = "MarkerView";
class Marker extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Marker() {
        this.mixins(['line', 'fill']);
        this.define({
            size: [p.DistanceSpec, { units: "screen", value: 4 }],
            angle: [p.AngleSpec, 0],
        });
    }
}
exports.Marker = Marker;
Marker.__name__ = "Marker";
Marker.init_Marker();
