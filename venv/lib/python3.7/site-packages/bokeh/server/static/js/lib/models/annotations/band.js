"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const column_data_source_1 = require("../sources/column_data_source");
const p = require("../../core/properties");
class BandView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
        this.set_data(this.model.source);
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.source.streaming, () => this.set_data(this.model.source));
        this.connect(this.model.source.patching, () => this.set_data(this.model.source));
        this.connect(this.model.source.change, () => this.set_data(this.model.source));
    }
    set_data(source) {
        super.set_data(source);
        this.visuals.warm_cache(source);
        this.plot_view.request_render();
    }
    _map_data() {
        const { frame } = this.plot_view;
        const dim = this.model.dimension;
        const xscale = frame.xscales[this.model.x_range_name];
        const yscale = frame.yscales[this.model.y_range_name];
        const limit_scale = dim == "height" ? yscale : xscale;
        const base_scale = dim == "height" ? xscale : yscale;
        const limit_view = dim == "height" ? frame.yview : frame.xview;
        const base_view = dim == "height" ? frame.xview : frame.yview;
        let _lower_sx;
        if (this.model.properties.lower.units == "data")
            _lower_sx = limit_scale.v_compute(this._lower);
        else
            _lower_sx = limit_view.v_compute(this._lower);
        let _upper_sx;
        if (this.model.properties.upper.units == "data")
            _upper_sx = limit_scale.v_compute(this._upper);
        else
            _upper_sx = limit_view.v_compute(this._upper);
        let _base_sx;
        if (this.model.properties.base.units == "data")
            _base_sx = base_scale.v_compute(this._base);
        else
            _base_sx = base_view.v_compute(this._base);
        const [i, j] = dim == 'height' ? [1, 0] : [0, 1];
        const _lower = [_lower_sx, _base_sx];
        const _upper = [_upper_sx, _base_sx];
        this._lower_sx = _lower[i];
        this._lower_sy = _lower[j];
        this._upper_sx = _upper[i];
        this._upper_sy = _upper[j];
    }
    render() {
        if (!this.model.visible)
            return;
        this._map_data();
        const { ctx } = this.plot_view.canvas_view;
        // Draw the band body
        ctx.beginPath();
        ctx.moveTo(this._lower_sx[0], this._lower_sy[0]);
        for (let i = 0, end = this._lower_sx.length; i < end; i++) {
            ctx.lineTo(this._lower_sx[i], this._lower_sy[i]);
        }
        // iterate backwards so that the upper end is below the lower start
        for (let start = this._upper_sx.length - 1, i = start; i >= 0; i--) {
            ctx.lineTo(this._upper_sx[i], this._upper_sy[i]);
        }
        ctx.closePath();
        if (this.visuals.fill.doit) {
            this.visuals.fill.set_value(ctx);
            ctx.fill();
        }
        // Draw the lower band edge
        ctx.beginPath();
        ctx.moveTo(this._lower_sx[0], this._lower_sy[0]);
        for (let i = 0, end = this._lower_sx.length; i < end; i++) {
            ctx.lineTo(this._lower_sx[i], this._lower_sy[i]);
        }
        if (this.visuals.line.doit) {
            this.visuals.line.set_value(ctx);
            ctx.stroke();
        }
        // Draw the upper band edge
        ctx.beginPath();
        ctx.moveTo(this._upper_sx[0], this._upper_sy[0]);
        for (let i = 0, end = this._upper_sx.length; i < end; i++) {
            ctx.lineTo(this._upper_sx[i], this._upper_sy[i]);
        }
        if (this.visuals.line.doit) {
            this.visuals.line.set_value(ctx);
            ctx.stroke();
        }
    }
}
exports.BandView = BandView;
BandView.__name__ = "BandView";
class Band extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Band() {
        this.prototype.default_view = BandView;
        this.mixins(['line', 'fill']);
        this.define({
            lower: [p.DistanceSpec],
            upper: [p.DistanceSpec],
            base: [p.DistanceSpec],
            dimension: [p.Dimension, 'height'],
            source: [p.Instance, () => new column_data_source_1.ColumnDataSource()],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
        this.override({
            fill_color: "#fff9ba",
            fill_alpha: 0.4,
            line_color: "#cccccc",
            line_alpha: 0.3,
        });
    }
}
exports.Band = Band;
Band.__name__ = "Band";
Band.init_Band();
