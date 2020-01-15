"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const spatial_1 = require("../../core/util/spatial");
const hittest = require("../../core/hittest");
const object_1 = require("../../core/util/object");
const array_1 = require("../../core/util/array");
const types_1 = require("../../core/util/types");
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
class MultiLineView extends glyph_1.GlyphView {
    _index_data() {
        const points = [];
        for (let i = 0, end = this._xs.length; i < end; i++) {
            if (this._xs[i] == null || this._xs[i].length === 0)
                continue;
            const _xsi = this._xs[i];
            const xs = [];
            for (let j = 0, n = _xsi.length; j < n; j++) {
                const x = _xsi[j];
                if (!types_1.isStrictNaN(x))
                    xs.push(x);
            }
            const _ysi = this._ys[i];
            const ys = [];
            for (let j = 0, n = _ysi.length; j < n; j++) {
                const y = _ysi[j];
                if (!types_1.isStrictNaN(y))
                    ys.push(y);
            }
            const [x0, x1] = [array_1.min(xs), array_1.max(xs)];
            const [y0, y1] = [array_1.min(ys), array_1.max(ys)];
            points.push({ x0, y0, x1, y1, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    _render(ctx, indices, { sxs, sys }) {
        for (const i of indices) {
            const [sx, sy] = [sxs[i], sys[i]];
            this.visuals.line.set_vectorize(ctx, i);
            for (let j = 0, end = sx.length; j < end; j++) {
                if (j == 0) {
                    ctx.beginPath();
                    ctx.moveTo(sx[j], sy[j]);
                    continue;
                }
                else if (isNaN(sx[j]) || isNaN(sy[j])) {
                    ctx.stroke();
                    ctx.beginPath();
                    continue;
                }
                else
                    ctx.lineTo(sx[j], sy[j]);
            }
            ctx.stroke();
        }
    }
    _hit_point(geometry) {
        const result = hittest.create_empty_hit_test_result();
        const point = { x: geometry.sx, y: geometry.sy };
        let shortest = 9999;
        const hits = {};
        for (let i = 0, end = this.sxs.length; i < end; i++) {
            const threshold = Math.max(2, this.visuals.line.cache_select('line_width', i) / 2);
            let points = null;
            for (let j = 0, endj = this.sxs[i].length - 1; j < endj; j++) {
                const p0 = { x: this.sxs[i][j], y: this.sys[i][j] };
                const p1 = { x: this.sxs[i][j + 1], y: this.sys[i][j + 1] };
                const dist = hittest.dist_to_segment(point, p0, p1);
                if (dist < threshold && dist < shortest) {
                    shortest = dist;
                    points = [j];
                }
            }
            if (points)
                hits[i] = points;
        }
        result.indices = object_1.keys(hits).map((x) => parseInt(x, 10));
        result.multiline_indices = hits;
        return result;
    }
    _hit_span(geometry) {
        const { sx, sy } = geometry;
        const result = hittest.create_empty_hit_test_result();
        let val;
        let values;
        if (geometry.direction === 'v') {
            val = this.renderer.yscale.invert(sy);
            values = this._ys;
        }
        else {
            val = this.renderer.xscale.invert(sx);
            values = this._xs;
        }
        const hits = {};
        for (let i = 0, end = values.length; i < end; i++) {
            const points = [];
            for (let j = 0, endj = values[i].length - 1; j < endj; j++) {
                if (values[i][j] <= val && val <= values[i][j + 1])
                    points.push(j);
            }
            if (points.length > 0)
                hits[i] = points;
        }
        result.indices = object_1.keys(hits).map((x) => parseInt(x, 10));
        result.multiline_indices = hits;
        return result;
    }
    get_interpolation_hit(i, point_i, geometry) {
        const [x2, y2, x3, y3] = [this._xs[i][point_i], this._ys[i][point_i], this._xs[i][point_i + 1], this._ys[i][point_i + 1]];
        return utils_1.line_interpolation(this.renderer, geometry, x2, y2, x3, y3);
    }
    draw_legend_for_index(ctx, bbox, index) {
        utils_1.generic_line_legend(this.visuals, ctx, bbox, index);
    }
    scenterx() {
        throw new Error("not implemented");
    }
    scentery() {
        throw new Error("not implemented");
    }
}
exports.MultiLineView = MultiLineView;
MultiLineView.__name__ = "MultiLineView";
class MultiLine extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_MultiLine() {
        this.prototype.default_view = MultiLineView;
        this.coords([['xs', 'ys']]);
        this.mixins(['line']);
    }
}
exports.MultiLine = MultiLine;
MultiLine.__name__ = "MultiLine";
MultiLine.init_MultiLine();
