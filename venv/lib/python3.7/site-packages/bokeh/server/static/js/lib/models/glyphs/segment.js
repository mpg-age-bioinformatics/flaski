"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const hittest = require("../../core/hittest");
const spatial_1 = require("../../core/util/spatial");
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
class SegmentView extends glyph_1.GlyphView {
    _index_data() {
        const points = [];
        for (let i = 0, end = this._x0.length; i < end; i++) {
            const x0 = this._x0[i];
            const x1 = this._x1[i];
            const y0 = this._y0[i];
            const y1 = this._y1[i];
            if (!isNaN(x0 + x1 + y0 + y1)) {
                points.push({
                    x0: Math.min(x0, x1),
                    y0: Math.min(y0, y1),
                    x1: Math.max(x0, x1),
                    y1: Math.max(y0, y1),
                    i,
                });
            }
        }
        return new spatial_1.SpatialIndex(points);
    }
    _render(ctx, indices, { sx0, sy0, sx1, sy1 }) {
        if (this.visuals.line.doit) {
            for (const i of indices) {
                if (isNaN(sx0[i] + sy0[i] + sx1[i] + sy1[i]))
                    continue;
                ctx.beginPath();
                ctx.moveTo(sx0[i], sy0[i]);
                ctx.lineTo(sx1[i], sy1[i]);
                this.visuals.line.set_vectorize(ctx, i);
                ctx.stroke();
            }
        }
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const point = { x: sx, y: sy };
        const hits = [];
        const lw_voffset = 2; // FIXME: Use maximum of segments line_width/2 instead of magic constant 2
        const [x0, x1] = this.renderer.xscale.r_invert(sx - lw_voffset, sx + lw_voffset);
        const [y0, y1] = this.renderer.yscale.r_invert(sy - lw_voffset, sy + lw_voffset);
        const candidates = this.index.indices({ x0, y0, x1, y1 });
        for (const i of candidates) {
            const threshold2 = Math.pow(Math.max(2, this.visuals.line.cache_select('line_width', i) / 2), 2);
            const p0 = { x: this.sx0[i], y: this.sy0[i] };
            const p1 = { x: this.sx1[i], y: this.sy1[i] };
            const dist2 = hittest.dist_to_segment_squared(point, p0, p1);
            if (dist2 < threshold2)
                hits.push(i);
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    _hit_span(geometry) {
        const [hr, vr] = this.renderer.plot_view.frame.bbox.ranges;
        const { sx, sy } = geometry;
        let v0;
        let v1;
        let val;
        if (geometry.direction == 'v') {
            val = this.renderer.yscale.invert(sy);
            [v0, v1] = [this._y0, this._y1];
        }
        else {
            val = this.renderer.xscale.invert(sx);
            [v0, v1] = [this._x0, this._x1];
        }
        const hits = [];
        const [x0, x1] = this.renderer.xscale.r_invert(hr.start, hr.end);
        const [y0, y1] = this.renderer.yscale.r_invert(vr.start, vr.end);
        const candidates = this.index.indices({ x0, y0, x1, y1 });
        for (const i of candidates) {
            if ((v0[i] <= val && val <= v1[i]) || (v1[i] <= val && val <= v0[i]))
                hits.push(i);
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    scenterx(i) {
        return (this.sx0[i] + this.sx1[i]) / 2;
    }
    scentery(i) {
        return (this.sy0[i] + this.sy1[i]) / 2;
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_line_legend(this.visuals, ctx, bbox, index);
    }
}
exports.SegmentView = SegmentView;
SegmentView.__name__ = "SegmentView";
class Segment extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Segment() {
        this.prototype.default_view = SegmentView;
        this.coords([['x0', 'y0'], ['x1', 'y1']]);
        this.mixins(['line']);
    }
}
exports.Segment = Segment;
Segment.__name__ = "Segment";
Segment.init_Segment();
