"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const xy_glyph_1 = require("./xy_glyph");
const hittest = require("../../core/hittest");
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
const arrayable_1 = require("../../core/util/arrayable");
class CircleView extends xy_glyph_1.XYGlyphView {
    _map_data() {
        // XXX: Order is important here: size is always present (at least
        // a default), but radius is only present if a user specifies it.
        if (this._radius != null) {
            if (this.model.properties.radius.spec.units == "data") {
                const rd = this.model.properties.radius_dimension.spec.value;
                switch (rd) {
                    case "x": {
                        this.sradius = this.sdist(this.renderer.xscale, this._x, this._radius);
                        break;
                    }
                    case "y": {
                        this.sradius = this.sdist(this.renderer.yscale, this._y, this._radius);
                        break;
                    }
                    case "max": {
                        const sradius_x = this.sdist(this.renderer.xscale, this._x, this._radius);
                        const sradius_y = this.sdist(this.renderer.yscale, this._y, this._radius);
                        this.sradius = arrayable_1.map(sradius_x, (s, i) => Math.max(s, sradius_y[i]));
                        break;
                    }
                    case "min": {
                        const sradius_x = this.sdist(this.renderer.xscale, this._x, this._radius);
                        const sradius_y = this.sdist(this.renderer.yscale, this._y, this._radius);
                        this.sradius = arrayable_1.map(sradius_x, (s, i) => Math.min(s, sradius_y[i]));
                        break;
                    }
                }
            }
            else {
                this.sradius = this._radius;
                this.max_size = 2 * this.max_radius;
            }
        }
        else
            this.sradius = arrayable_1.map(this._size, (s) => s / 2);
    }
    _mask_data() {
        const [hr, vr] = this.renderer.plot_view.frame.bbox.ranges;
        let x0, y0;
        let x1, y1;
        if (this._radius != null && this.model.properties.radius.units == "data") {
            const sx0 = hr.start;
            const sx1 = hr.end;
            [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
            x0 -= this.max_radius;
            x1 += this.max_radius;
            const sy0 = vr.start;
            const sy1 = vr.end;
            [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
            y0 -= this.max_radius;
            y1 += this.max_radius;
        }
        else {
            const sx0 = hr.start - this.max_size;
            const sx1 = hr.end + this.max_size;
            [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
            const sy0 = vr.start - this.max_size;
            const sy1 = vr.end + this.max_size;
            [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
        }
        return this.index.indices({ x0, x1, y0, y1 });
    }
    _render(ctx, indices, { sx, sy, sradius }) {
        for (const i of indices) {
            if (isNaN(sx[i] + sy[i] + sradius[i]))
                continue;
            ctx.beginPath();
            ctx.arc(sx[i], sy[i], sradius[i], 0, 2 * Math.PI, false);
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
        let dist, r2, sx0, sx1, sy0, sy1, x0, x1, y0, y1;
        const { sx, sy } = geometry;
        const x = this.renderer.xscale.invert(sx);
        const y = this.renderer.yscale.invert(sy);
        // check radius first
        if ((this._radius != null) && (this.model.properties.radius.units == "data")) {
            x0 = x - this.max_radius;
            x1 = x + this.max_radius;
            y0 = y - this.max_radius;
            y1 = y + this.max_radius;
        }
        else {
            sx0 = sx - this.max_size;
            sx1 = sx + this.max_size;
            [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
            [x0, x1] = [Math.min(x0, x1), Math.max(x0, x1)];
            sy0 = sy - this.max_size;
            sy1 = sy + this.max_size;
            [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
            [y0, y1] = [Math.min(y0, y1), Math.max(y0, y1)];
        }
        const candidates = this.index.indices({ x0, x1, y0, y1 });
        const hits = [];
        if ((this._radius != null) && (this.model.properties.radius.units == "data")) {
            for (const i of candidates) {
                r2 = Math.pow(this.sradius[i], 2);
                [sx0, sx1] = this.renderer.xscale.r_compute(x, this._x[i]);
                [sy0, sy1] = this.renderer.yscale.r_compute(y, this._y[i]);
                dist = Math.pow(sx0 - sx1, 2) + Math.pow(sy0 - sy1, 2);
                if (dist <= r2) {
                    hits.push([i, dist]);
                }
            }
        }
        else {
            for (const i of candidates) {
                r2 = Math.pow(this.sradius[i], 2);
                dist = Math.pow(this.sx[i] - sx, 2) + Math.pow(this.sy[i] - sy, 2);
                if (dist <= r2) {
                    hits.push([i, dist]);
                }
            }
        }
        return hittest.create_hit_test_result_from_hits(hits);
    }
    _hit_span(geometry) {
        const { sx, sy } = geometry;
        const bounds = this.bounds();
        const result = hittest.create_empty_hit_test_result();
        let x0, x1, y0, y1;
        if (geometry.direction == 'h') {
            // use circle bounds instead of current pointer y coordinates
            let sx0, sx1;
            y0 = bounds.y0;
            y1 = bounds.y1;
            if (this._radius != null && this.model.properties.radius.units == "data") {
                sx0 = sx - this.max_radius;
                sx1 = sx + this.max_radius;
                [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
            }
            else {
                const ms = this.max_size / 2;
                sx0 = sx - ms;
                sx1 = sx + ms;
                [x0, x1] = this.renderer.xscale.r_invert(sx0, sx1);
            }
        }
        else {
            // use circle bounds instead of current pointer x coordinates
            let sy0, sy1;
            x0 = bounds.x0;
            x1 = bounds.x1;
            if (this._radius != null && this.model.properties.radius.units == "data") {
                sy0 = sy - this.max_radius;
                sy1 = sy + this.max_radius;
                [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
            }
            else {
                const ms = this.max_size / 2;
                sy0 = sy - ms;
                sy1 = sy + ms;
                [y0, y1] = this.renderer.yscale.r_invert(sy0, sy1);
            }
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
            if (hittest.point_in_poly(this.sx[i], this.sy[i], sx, sy)) {
                hits.push(idx);
            }
        }
        const result = hittest.create_empty_hit_test_result();
        result.indices = hits;
        return result;
    }
    // circle does not inherit from marker (since it also accepts radius) so we
    // must supply a draw_legend for it  here
    draw_legend_for_index(ctx, { x0, y0, x1, y1 }, index) {
        // using objects like this seems a little wonky, since the keys are coerced to
        // stings, but it works
        const len = index + 1;
        const sx = new Array(len);
        sx[index] = (x0 + x1) / 2;
        const sy = new Array(len);
        sy[index] = (y0 + y1) / 2;
        const sradius = new Array(len);
        sradius[index] = Math.min(Math.abs(x1 - x0), Math.abs(y1 - y0)) * 0.2;
        this._render(ctx, [index], { sx, sy, sradius }); // XXX
    }
}
exports.CircleView = CircleView;
CircleView.__name__ = "CircleView";
class Circle extends xy_glyph_1.XYGlyph {
    constructor(attrs) {
        super(attrs);
    }
    static init_Circle() {
        this.prototype.default_view = CircleView;
        this.mixins(['line', 'fill']);
        this.define({
            angle: [p.AngleSpec, 0],
            size: [p.DistanceSpec, { units: "screen", value: 4 }],
            radius: [p.DistanceSpec],
            radius_dimension: [p.RadiusDimension, 'x'],
        });
    }
    initialize() {
        super.initialize();
        this.properties.radius.optional = true;
    }
}
exports.Circle = Circle;
Circle.__name__ = "Circle";
Circle.init_Circle();
