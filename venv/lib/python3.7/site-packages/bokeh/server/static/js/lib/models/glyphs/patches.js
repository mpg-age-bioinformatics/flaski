"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const spatial_1 = require("../../core/util/spatial");
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
const array_1 = require("../../core/util/array");
const arrayable_1 = require("../../core/util/arrayable");
const types_1 = require("../../core/util/types");
const hittest = require("../../core/hittest");
class PatchesView extends glyph_1.GlyphView {
    _build_discontinuous_object(nanned_qs) {
        // _s is this.xs, this.ys, this.sxs, this.sys
        // an object of n 1-d arrays in either data or screen units
        //
        // Each 1-d array gets broken to an array of arrays split
        // on any NaNs
        //
        // So:
        // { 0: [x11, x12],
        //   1: [x21, x22, x23],
        //   2: [x31, NaN, x32]
        // }
        // becomes
        // { 0: [[x11, x12]],
        //   1: [[x21, x22, x23]],
        //   2: [[x31],[x32]]
        // }
        const ds = [];
        for (let i = 0, end = nanned_qs.length; i < end; i++) {
            ds[i] = [];
            let qs = array_1.copy(nanned_qs[i]);
            while (qs.length > 0) {
                const nan_index = array_1.find_last_index(qs, (q) => types_1.isStrictNaN(q));
                let qs_part;
                if (nan_index >= 0)
                    qs_part = qs.splice(nan_index);
                else {
                    qs_part = qs;
                    qs = [];
                }
                const denanned = qs_part.filter((q) => !types_1.isStrictNaN(q));
                ds[i].push(denanned);
            }
        }
        return ds;
    }
    _index_data() {
        const xss = this._build_discontinuous_object(this._xs); // XXX
        const yss = this._build_discontinuous_object(this._ys); // XXX
        const points = [];
        for (let i = 0, end = this._xs.length; i < end; i++) {
            for (let j = 0, endj = xss[i].length; j < endj; j++) {
                const xs = xss[i][j];
                const ys = yss[i][j];
                if (xs.length == 0)
                    continue;
                points.push({ x0: array_1.min(xs), y0: array_1.min(ys), x1: array_1.max(xs), y1: array_1.max(ys), i });
            }
        }
        return new spatial_1.SpatialIndex(points);
    }
    _mask_data() {
        const xr = this.renderer.plot_view.frame.x_ranges.default;
        const [x0, x1] = [xr.min, xr.max];
        const yr = this.renderer.plot_view.frame.y_ranges.default;
        const [y0, y1] = [yr.min, yr.max];
        const indices = this.index.indices({ x0, x1, y0, y1 });
        // TODO (bev) this should be under test
        return indices.sort((a, b) => a - b);
    }
    _inner_loop(ctx, sx, sy, func) {
        for (let j = 0, end = sx.length; j < end; j++) {
            if (j == 0) {
                ctx.beginPath();
                ctx.moveTo(sx[j], sy[j]);
                continue;
            }
            else if (isNaN(sx[j] + sy[j])) {
                ctx.closePath();
                func.apply(ctx);
                ctx.beginPath();
                continue;
            }
            else
                ctx.lineTo(sx[j], sy[j]);
        }
        ctx.closePath();
        func.call(ctx);
    }
    _render(ctx, indices, { sxs, sys }) {
        // this.sxss and this.syss are used by _hit_point and sxc, syc
        // This is the earliest we can build them, and only build them once
        this.sxss = this._build_discontinuous_object(sxs); // XXX
        this.syss = this._build_discontinuous_object(sys); // XXX
        for (const i of indices) {
            const [sx, sy] = [sxs[i], sys[i]];
            if (this.visuals.fill.doit) {
                this.visuals.fill.set_vectorize(ctx, i);
                this._inner_loop(ctx, sx, sy, ctx.fill);
            }
            this.visuals.hatch.doit2(ctx, i, () => this._inner_loop(ctx, sx, sy, ctx.fill), () => this.renderer.request_render());
            if (this.visuals.line.doit) {
                this.visuals.line.set_vectorize(ctx, i);
                this._inner_loop(ctx, sx, sy, ctx.stroke);
            }
        }
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const x = this.renderer.xscale.invert(sx);
        const y = this.renderer.yscale.invert(sy);
        const candidates = this.index.indices({ x0: x, y0: y, x1: x, y1: y });
        const hits = [];
        for (let i = 0, end = candidates.length; i < end; i++) {
            const idx = candidates[i];
            const sxs = this.sxss[idx];
            const sys = this.syss[idx];
            for (let j = 0, endj = sxs.length; j < endj; j++) {
                if (hittest.point_in_poly(sx, sy, sxs[j], sys[j])) {
                    hits.push(idx);
                }
            }
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    _get_snap_coord(array) {
        return arrayable_1.sum(array) / array.length;
    }
    scenterx(i, sx, sy) {
        if (this.sxss[i].length == 1) {
            // We don't have discontinuous objects so we're ok
            return this._get_snap_coord(this.sxs[i]);
        }
        else {
            // We have discontinuous objects, so we need to find which
            // one we're in, we can use point_in_poly again
            const sxs = this.sxss[i];
            const sys = this.syss[i];
            for (let j = 0, end = sxs.length; j < end; j++) {
                if (hittest.point_in_poly(sx, sy, sxs[j], sys[j]))
                    return this._get_snap_coord(sxs[j]);
            }
        }
        throw new Error("unreachable code");
    }
    scentery(i, sx, sy) {
        if (this.syss[i].length == 1) {
            // We don't have discontinuous objects so we're ok
            return this._get_snap_coord(this.sys[i]);
        }
        else {
            // We have discontinuous objects, so we need to find which
            // one we're in, we can use point_in_poly again
            const sxs = this.sxss[i];
            const sys = this.syss[i];
            for (let j = 0, end = sxs.length; j < end; j++) {
                if (hittest.point_in_poly(sx, sy, sxs[j], sys[j]))
                    return this._get_snap_coord(sys[j]);
            }
        }
        throw new Error("unreachable code");
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_area_legend(this.visuals, ctx, bbox, index);
    }
}
exports.PatchesView = PatchesView;
PatchesView.__name__ = "PatchesView";
class Patches extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Patches() {
        this.prototype.default_view = PatchesView;
        this.coords([['xs', 'ys']]);
        this.mixins(['line', 'fill', 'hatch']);
    }
}
exports.Patches = Patches;
Patches.__name__ = "Patches";
Patches.init_Patches();
