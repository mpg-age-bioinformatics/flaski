"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const p = require("../../core/properties");
class SlopeView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.plot_view.request_render());
    }
    render() {
        if (!this.model.visible)
            return;
        this._draw_slope();
    }
    _draw_slope() {
        const gradient = this.model.gradient;
        const y_intercept = this.model.y_intercept;
        if (gradient == null || y_intercept == null) {
            return;
        }
        const { frame } = this.plot_view;
        const xscale = frame.xscales[this.model.x_range_name];
        const yscale = frame.yscales[this.model.y_range_name];
        const sy_start = frame._top.value;
        const sy_end = sy_start + frame._height.value;
        const y_start = yscale.invert(sy_start);
        const y_end = yscale.invert(sy_end);
        const x_start = (y_start - y_intercept) / gradient;
        const x_end = (y_end - y_intercept) / gradient;
        const sx_start = xscale.compute(x_start);
        const sx_end = xscale.compute(x_end);
        const { ctx } = this.plot_view.canvas_view;
        ctx.save();
        ctx.beginPath();
        this.visuals.line.set_value(ctx);
        ctx.moveTo(sx_start, sy_start);
        ctx.lineTo(sx_end, sy_end);
        ctx.stroke();
        ctx.restore();
    }
}
exports.SlopeView = SlopeView;
SlopeView.__name__ = "SlopeView";
class Slope extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Slope() {
        this.prototype.default_view = SlopeView;
        this.mixins(['line']);
        this.define({
            gradient: [p.Number, null],
            y_intercept: [p.Number, null],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
        this.override({
            line_color: 'black',
        });
    }
}
exports.Slope = Slope;
Slope.__name__ = "Slope";
Slope.init_Slope();
