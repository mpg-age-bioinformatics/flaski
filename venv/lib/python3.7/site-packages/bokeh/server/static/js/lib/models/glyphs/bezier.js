"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const spatial_1 = require("../../core/util/spatial");
const glyph_1 = require("./glyph");
const utils_1 = require("./utils");
// algorithm adapted from http://stackoverflow.com/a/14429749/3406693
function _cbb(x0, y0, x1, y1, x2, y2, x3, y3) {
    const tvalues = [];
    const bounds = [[], []];
    for (let i = 0; i <= 2; i++) {
        let a, b, c;
        if (i === 0) {
            b = ((6 * x0) - (12 * x1)) + (6 * x2);
            a = (((-3 * x0) + (9 * x1)) - (9 * x2)) + (3 * x3);
            c = (3 * x1) - (3 * x0);
        }
        else {
            b = ((6 * y0) - (12 * y1)) + (6 * y2);
            a = (((-3 * y0) + (9 * y1)) - (9 * y2)) + (3 * y3);
            c = (3 * y1) - (3 * y0);
        }
        if (Math.abs(a) < 1e-12) { // Numerical robustness
            if (Math.abs(b) < 1e-12) // Numerical robustness
                continue;
            const t = -c / b;
            if (0 < t && t < 1)
                tvalues.push(t);
            continue;
        }
        const b2ac = (b * b) - (4 * c * a);
        const sqrtb2ac = Math.sqrt(b2ac);
        if (b2ac < 0)
            continue;
        const t1 = (-b + sqrtb2ac) / (2 * a);
        if (0 < t1 && t1 < 1)
            tvalues.push(t1);
        const t2 = (-b - sqrtb2ac) / (2 * a);
        if (0 < t2 && t2 < 1)
            tvalues.push(t2);
    }
    let j = tvalues.length;
    const jlen = j;
    while (j--) {
        const t = tvalues[j];
        const mt = 1 - t;
        const x = (mt * mt * mt * x0) + (3 * mt * mt * t * x1) + (3 * mt * t * t * x2) + (t * t * t * x3);
        bounds[0][j] = x;
        const y = (mt * mt * mt * y0) + (3 * mt * mt * t * y1) + (3 * mt * t * t * y2) + (t * t * t * y3);
        bounds[1][j] = y;
    }
    bounds[0][jlen] = x0;
    bounds[1][jlen] = y0;
    bounds[0][jlen + 1] = x3;
    bounds[1][jlen + 1] = y3;
    return [
        Math.min(...bounds[0]),
        Math.max(...bounds[1]),
        Math.max(...bounds[0]),
        Math.min(...bounds[1]),
    ];
}
class BezierView extends glyph_1.GlyphView {
    _index_data() {
        const points = [];
        for (let i = 0, end = this._x0.length; i < end; i++) {
            if (isNaN(this._x0[i] + this._x1[i] + this._y0[i] + this._y1[i] + this._cx0[i] + this._cy0[i] + this._cx1[i] + this._cy1[i]))
                continue;
            const [x0, y0, x1, y1] = _cbb(this._x0[i], this._y0[i], this._x1[i], this._y1[i], this._cx0[i], this._cy0[i], this._cx1[i], this._cy1[i]);
            points.push({ x0, y0, x1, y1, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    _render(ctx, indices, { sx0, sy0, sx1, sy1, scx0, scy0, scx1, scy1 }) {
        if (this.visuals.line.doit) {
            for (const i of indices) {
                if (isNaN(sx0[i] + sy0[i] + sx1[i] + sy1[i] + scx0[i] + scy0[i] + scx1[i] + scy1[i]))
                    continue;
                ctx.beginPath();
                ctx.moveTo(sx0[i], sy0[i]);
                ctx.bezierCurveTo(scx0[i], scy0[i], scx1[i], scy1[i], sx1[i], sy1[i]);
                this.visuals.line.set_vectorize(ctx, i);
                ctx.stroke();
            }
        }
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
exports.BezierView = BezierView;
BezierView.__name__ = "BezierView";
class Bezier extends glyph_1.Glyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Bezier() {
        this.prototype.default_view = BezierView;
        this.coords([['x0', 'y0'], ['x1', 'y1'], ['cx0', 'cy0'], ['cx1', 'cy1']]);
        this.mixins(['line']);
    }
}
exports.Bezier = Bezier;
Bezier.__name__ = "Bezier";
Bezier.init_Bezier();
