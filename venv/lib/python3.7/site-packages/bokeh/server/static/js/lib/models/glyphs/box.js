"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const spatial_1 = require("../../core/util/spatial");
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
const hittest = require("../../core/hittest");
class BoxView extends glyph_1.GlyphView {
    get_anchor_point(anchor, i, _spt) {
        const left = Math.min(this.sleft[i], this.sright[i]);
        const right = Math.max(this.sright[i], this.sleft[i]);
        const top = Math.min(this.stop[i], this.sbottom[i]); // screen coordinates !!!
        const bottom = Math.max(this.sbottom[i], this.stop[i]); //
        switch (anchor) {
            case "top_left": return { x: left, y: top };
            case "top_center": return { x: (left + right) / 2, y: top };
            case "top_right": return { x: right, y: top };
            case "bottom_left": return { x: left, y: bottom };
            case "bottom_center": return { x: (left + right) / 2, y: bottom };
            case "bottom_right": return { x: right, y: bottom };
            case "center_left": return { x: left, y: (top + bottom) / 2 };
            case "center": return { x: (left + right) / 2, y: (top + bottom) / 2 };
            case "center_right": return { x: right, y: (top + bottom) / 2 };
            default: return null;
        }
    }
    _index_box(len) {
        const points = [];
        for (let i = 0; i < len; i++) {
            const [l, r, t, b] = this._lrtb(i);
            if (isNaN(l + r + t + b) || !isFinite(l + r + t + b))
                continue;
            points.push({
                x0: Math.min(l, r),
                y0: Math.min(t, b),
                x1: Math.max(r, l),
                y1: Math.max(t, b),
                i,
            });
        }
        return new spatial_1.SpatialIndex(points);
    }
    _render(ctx, indices, { sleft, sright, stop, sbottom }) {
        for (const i of indices) {
            if (isNaN(sleft[i] + stop[i] + sright[i] + sbottom[i]))
                continue;
            ctx.rect(sleft[i], stop[i], sright[i] - sleft[i], sbottom[i] - stop[i]);
            if (this.visuals.fill.doit) {
                this.visuals.fill.set_vectorize(ctx, i);
                ctx.beginPath();
                ctx.rect(sleft[i], stop[i], sright[i] - sleft[i], sbottom[i] - stop[i]);
                ctx.fill();
            }
            this.visuals.hatch.doit2(ctx, i, () => {
                ctx.beginPath();
                ctx.rect(sleft[i], stop[i], sright[i] - sleft[i], sbottom[i] - stop[i]);
                ctx.fill();
            }, () => this.renderer.request_render());
            if (this.visuals.line.doit) {
                this.visuals.line.set_vectorize(ctx, i);
                ctx.beginPath();
                ctx.rect(sleft[i], stop[i], sright[i] - sleft[i], sbottom[i] - stop[i]);
                ctx.stroke();
            }
        }
    }
    // We need to clamp the endpoints inside the viewport, because various browser canvas
    // implementations have issues drawing rects with enpoints far outside the viewport
    _clamp_viewport() {
        const hr = this.renderer.plot_view.frame.bbox.h_range;
        const vr = this.renderer.plot_view.frame.bbox.v_range;
        const n = this.stop.length;
        for (let i = 0; i < n; i++) {
            this.stop[i] = Math.max(this.stop[i], vr.start);
            this.sbottom[i] = Math.min(this.sbottom[i], vr.end);
            this.sleft[i] = Math.max(this.sleft[i], hr.start);
            this.sright[i] = Math.min(this.sright[i], hr.end);
        }
    }
    _hit_rect(geometry) {
        return this._hit_rect_against_index(geometry);
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const x = this.renderer.xscale.invert(sx);
        const y = this.renderer.yscale.invert(sy);
        const hits = this.index.indices({ x0: x, y0: y, x1: x, y1: y });
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    _hit_span(geometry) {
        const { sx, sy } = geometry;
        let hits;
        if (geometry.direction == 'v') {
            const y = this.renderer.yscale.invert(sy);
            const hr = this.renderer.plot_view.frame.bbox.h_range;
            const [x0, x1] = this.renderer.xscale.r_invert(hr.start, hr.end);
            hits = this.index.indices({ x0, y0: y, x1, y1: y });
        }
        else {
            const x = this.renderer.xscale.invert(sx);
            const vr = this.renderer.plot_view.frame.bbox.v_range;
            const [y0, y1] = this.renderer.yscale.r_invert(vr.start, vr.end);
            hits = this.index.indices({ x0: x, y0, x1: x, y1 });
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_area_legend(this.visuals, ctx, bbox, index);
    }
}
exports.BoxView = BoxView;
BoxView.__name__ = "BoxView";
class Box extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Box() {
        this.mixins(['line', 'fill', 'hatch']);
    }
}
exports.Box = Box;
Box.__name__ = "Box";
Box.init_Box();
