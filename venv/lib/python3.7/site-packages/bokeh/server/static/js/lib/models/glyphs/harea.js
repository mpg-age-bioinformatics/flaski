"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const area_1 = require("./area");
const spatial_1 = require("../../core/util/spatial");
const hittest = require("../../core/hittest");
const p = require("../../core/properties");
class HAreaView extends area_1.AreaView {
    _index_data() {
        const points = [];
        for (let i = 0, end = this._x1.length; i < end; i++) {
            const x1 = this._x1[i];
            const x2 = this._x2[i];
            const y = this._y[i];
            if (isNaN(x1 + x2 + y) || !isFinite(x1 + x2 + y))
                continue;
            points.push({ x0: Math.min(x1, x2), y0: y, x1: Math.max(x1, x2), y1: y, i });
        }
        return new spatial_1.SpatialIndex(points);
    }
    _inner(ctx, sx1, sx2, sy, func) {
        ctx.beginPath();
        for (let i = 0, end = sx1.length; i < end; i++) {
            ctx.lineTo(sx1[i], sy[i]);
        }
        // iterate backwards so that the upper end is below the lower start
        for (let start = sx2.length - 1, i = start; i >= 0; i--) {
            ctx.lineTo(sx2[i], sy[i]);
        }
        ctx.closePath();
        func.call(ctx);
    }
    _render(ctx, _indices, { sx1, sx2, sy }) {
        if (this.visuals.fill.doit) {
            this.visuals.fill.set_value(ctx);
            this._inner(ctx, sx1, sx2, sy, ctx.fill);
        }
        this.visuals.hatch.doit2(ctx, 0, () => this._inner(ctx, sx1, sx2, sy, ctx.fill), () => this.renderer.request_render());
    }
    _hit_point(geometry) {
        const result = hittest.create_empty_hit_test_result();
        const L = this.sy.length;
        const sx = new Float64Array(2 * L);
        const sy = new Float64Array(2 * L);
        for (let i = 0, end = L; i < end; i++) {
            sx[i] = this.sx1[i];
            sy[i] = this.sy[i];
            sx[L + i] = this.sx2[L - i - 1];
            sy[L + i] = this.sy[L - i - 1];
        }
        if (hittest.point_in_poly(geometry.sx, geometry.sy, sx, sy)) {
            result.add_to_selected_glyphs(this.model);
            result.get_view = () => this;
        }
        return result;
    }
    scenterx(i) {
        return (this.sx1[i] + this.sx2[i]) / 2;
    }
    scentery(i) {
        return this.sy[i];
    }
    _map_data() {
        this.sx1 = this.renderer.xscale.v_compute(this._x1);
        this.sx2 = this.renderer.xscale.v_compute(this._x2);
        this.sy = this.renderer.yscale.v_compute(this._y);
    }
}
exports.HAreaView = HAreaView;
HAreaView.__name__ = "HAreaView";
class HArea extends area_1.Area {
    constructor(attrs) {
        super(attrs);
    }
    static init_HArea() {
        this.prototype.default_view = HAreaView;
        this.define({
            x1: [p.CoordinateSpec],
            x2: [p.CoordinateSpec],
            y: [p.CoordinateSpec],
        });
    }
}
exports.HArea = HArea;
HArea.__name__ = "HArea";
HArea.init_HArea();
