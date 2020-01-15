"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const column_data_source_1 = require("../sources/column_data_source");
const arrow_head_1 = require("./arrow_head");
const p = require("../../core/properties");
class WhiskerView extends annotation_1.AnnotationView {
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
        if (this.visuals.line.doit) {
            for (let i = 0, end = this._lower_sx.length; i < end; i++) {
                this.visuals.line.set_vectorize(ctx, i);
                ctx.beginPath();
                ctx.moveTo(this._lower_sx[i], this._lower_sy[i]);
                ctx.lineTo(this._upper_sx[i], this._upper_sy[i]);
                ctx.stroke();
            }
        }
        const angle = this.model.dimension == "height" ? 0 : Math.PI / 2;
        if (this.model.lower_head != null) {
            for (let i = 0, end = this._lower_sx.length; i < end; i++) {
                ctx.save();
                ctx.translate(this._lower_sx[i], this._lower_sy[i]);
                ctx.rotate(angle + Math.PI);
                this.model.lower_head.render(ctx, i);
                ctx.restore();
            }
        }
        if (this.model.upper_head != null) {
            for (let i = 0, end = this._upper_sx.length; i < end; i++) {
                ctx.save();
                ctx.translate(this._upper_sx[i], this._upper_sy[i]);
                ctx.rotate(angle);
                this.model.upper_head.render(ctx, i);
                ctx.restore();
            }
        }
    }
}
exports.WhiskerView = WhiskerView;
WhiskerView.__name__ = "WhiskerView";
class Whisker extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Whisker() {
        this.prototype.default_view = WhiskerView;
        this.mixins(['line']);
        this.define({
            lower: [p.DistanceSpec],
            lower_head: [p.Instance, () => new arrow_head_1.TeeHead({ level: "underlay", size: 10 })],
            upper: [p.DistanceSpec],
            upper_head: [p.Instance, () => new arrow_head_1.TeeHead({ level: "underlay", size: 10 })],
            base: [p.DistanceSpec],
            dimension: [p.Dimension, 'height'],
            source: [p.Instance, () => new column_data_source_1.ColumnDataSource()],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
        this.override({
            level: 'underlay',
        });
    }
}
exports.Whisker = Whisker;
Whisker.__name__ = "Whisker";
Whisker.init_Whisker();
