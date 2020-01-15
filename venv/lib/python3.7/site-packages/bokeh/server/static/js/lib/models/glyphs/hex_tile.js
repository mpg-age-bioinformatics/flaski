"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const glyph_1 = require("./glyph");
const hittest = require("../../core/hittest");
const p = require("../../core/properties");
const spatial_1 = require("../../core/util/spatial");
const utils_1 = require("./utils");
class HexTileView extends glyph_1.GlyphView {
    scenterx(i) { return this.sx[i]; }
    scentery(i) { return this.sy[i]; }
    _set_data() {
        const n = this._q.length;
        const size = this.model.size;
        const aspect_scale = this.model.aspect_scale;
        this._x = new Float64Array(n);
        this._y = new Float64Array(n);
        if (this.model.orientation == "pointytop") {
            for (let i = 0; i < n; i++) {
                this._x[i] = size * Math.sqrt(3) * (this._q[i] + this._r[i] / 2) / aspect_scale;
                this._y[i] = -size * 3 / 2 * this._r[i];
            }
        }
        else {
            for (let i = 0; i < n; i++) {
                this._x[i] = size * 3 / 2 * this._q[i];
                this._y[i] = -size * Math.sqrt(3) * (this._r[i] + this._q[i] / 2) * aspect_scale;
            }
        }
    }
    _index_data() {
        let ysize = this.model.size;
        let xsize = Math.sqrt(3) * ysize / 2;
        if (this.model.orientation == "flattop") {
            [xsize, ysize] = [ysize, xsize];
            ysize *= this.model.aspect_scale;
        }
        else
            xsize /= this.model.aspect_scale;
        const points = [];
        for (let i = 0; i < this._x.length; i++) {
            const x = this._x[i];
            const y = this._y[i];
            if (isNaN(x + y) || !isFinite(x + y))
                continue;
            points.push({ x0: x - xsize, y0: y - ysize, x1: x + xsize, y1: y + ysize, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    // overriding map_data instead of _map_data because the default automatic mappings
    // for other glyphs (with cartesian coordinates) is not useful
    map_data() {
        [this.sx, this.sy] = this.map_to_screen(this._x, this._y);
        [this.svx, this.svy] = this._get_unscaled_vertices();
    }
    _get_unscaled_vertices() {
        const size = this.model.size;
        const aspect_scale = this.model.aspect_scale;
        if (this.model.orientation == "pointytop") {
            const rscale = this.renderer.yscale;
            const hscale = this.renderer.xscale;
            const r = Math.abs(rscale.compute(0) - rscale.compute(size)); // assumes linear scale
            const h = Math.sqrt(3) / 2 * Math.abs(hscale.compute(0) - hscale.compute(size)) / aspect_scale; // assumes linear scale
            const r2 = r / 2.0;
            const svx = [0, -h, -h, 0, h, h];
            const svy = [r, r2, -r2, -r, -r2, r2];
            return [svx, svy];
        }
        else {
            const rscale = this.renderer.xscale;
            const hscale = this.renderer.yscale;
            const r = Math.abs(rscale.compute(0) - rscale.compute(size)); // assumes linear scale
            const h = Math.sqrt(3) / 2 * Math.abs(hscale.compute(0) - hscale.compute(size)) * aspect_scale; // assumes linear scale
            const r2 = r / 2.0;
            const svx = [r, r2, -r2, -r, -r2, r2];
            const svy = [0, -h, -h, 0, h, h];
            return [svx, svy];
        }
    }
    _render(ctx, indices, { sx, sy, svx, svy, _scale }) {
        for (const i of indices) {
            if (isNaN(sx[i] + sy[i] + _scale[i]))
                continue;
            ctx.translate(sx[i], sy[i]);
            ctx.beginPath();
            for (let j = 0; j < 6; j++) {
                ctx.lineTo(svx[j] * _scale[i], svy[j] * _scale[i]);
            }
            ctx.closePath();
            ctx.translate(-sx[i], -sy[i]);
            if (this.visuals.fill.doit) {
                this.visuals.fill.set_vectorize(ctx, i);
                ctx.fill();
            }
            if (this.visuals.line.doit) {
                this.visuals.line.set_vectorize(ctx, i);
                ctx.stroke();
            }
        }
    }
    _hit_point(geometry) {
        const { sx, sy } = geometry;
        const x = this.renderer.xscale.invert(sx);
        const y = this.renderer.yscale.invert(sy);
        const candidates = this.index.indices({ x0: x, y0: y, x1: x, y1: y });
        const hits = [];
        for (const i of candidates) {
            if (hittest.point_in_poly(sx - this.sx[i], sy - this.sy[i], this.svx, this.svy)) {
                hits.push(i);
            }
        }
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
    _hit_rect(geometry) {
        const { sx0, sx1, sy0, sy1 } = geometry;
        const [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
        const [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        const result = hittest.create_empty_hit_test_result();
        result.indices = this.index.indices({ x0, x1, y0, y1 });
        return result;
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_area_legend(this.visuals, ctx, bbox, index);
    }
}
exports.HexTileView = HexTileView;
HexTileView.__name__ = "HexTileView";
class HexTile extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_HexTile() {
        this.prototype.default_view = HexTileView;
        this.coords([['r', 'q']]);
        this.mixins(['line', 'fill']);
        this.define({
            size: [p.Number, 1.0],
            aspect_scale: [p.Number, 1.0],
            scale: [p.NumberSpec, 1.0],
            orientation: [p.HexTileOrientation, "pointytop"],
        });
        this.override({ line_color: null });
    }
}
exports.HexTile = HexTile;
HexTile.__name__ = "HexTile";
HexTile.init_HexTile();
