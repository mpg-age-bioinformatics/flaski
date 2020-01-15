"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
class SpanView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
        this.plot_view.canvas_overlays.appendChild(this.el);
        this.el.style.position = "absolute";
        dom_1.undisplay(this.el);
    }
    connect_signals() {
        super.connect_signals();
        if (this.model.for_hover)
            this.connect(this.model.properties.computed_location.change, () => this._draw_span());
        else {
            if (this.model.render_mode == 'canvas') {
                this.connect(this.model.change, () => this.plot_view.request_render());
                this.connect(this.model.properties.location.change, () => this.plot_view.request_render());
            }
            else {
                this.connect(this.model.change, () => this.render());
                this.connect(this.model.properties.location.change, () => this._draw_span());
            }
        }
    }
    render() {
        if (!this.model.visible && this.model.render_mode == 'css')
            dom_1.undisplay(this.el);
        if (!this.model.visible)
            return;
        this._draw_span();
    }
    _draw_span() {
        const loc = this.model.for_hover ? this.model.computed_location : this.model.location;
        if (loc == null) {
            dom_1.undisplay(this.el);
            return;
        }
        const { frame } = this.plot_view;
        const xscale = frame.xscales[this.model.x_range_name];
        const yscale = frame.yscales[this.model.y_range_name];
        const _calc_dim = (scale, view) => {
            if (this.model.for_hover)
                return this.model.computed_location;
            else {
                if (this.model.location_units == 'data')
                    return scale.compute(loc);
                else
                    return view.compute(loc);
            }
        };
        let height, sleft, stop, width;
        if (this.model.dimension == 'width') {
            stop = _calc_dim(yscale, frame.yview);
            sleft = frame._left.value;
            width = frame._width.value;
            height = this.model.properties.line_width.value();
        }
        else {
            stop = frame._top.value;
            sleft = _calc_dim(xscale, frame.xview);
            width = this.model.properties.line_width.value();
            height = frame._height.value;
        }
        if (this.model.render_mode == "css") {
            this.el.style.top = `${stop}px`;
            this.el.style.left = `${sleft}px`;
            this.el.style.width = `${width}px`;
            this.el.style.height = `${height}px`;
            this.el.style.backgroundColor = this.model.properties.line_color.value();
            this.el.style.opacity = this.model.properties.line_alpha.value();
            dom_1.display(this.el);
        }
        else if (this.model.render_mode == "canvas") {
            const { ctx } = this.plot_view.canvas_view;
            ctx.save();
            ctx.beginPath();
            this.visuals.line.set_value(ctx);
            ctx.moveTo(sleft, stop);
            if (this.model.dimension == "width") {
                ctx.lineTo(sleft + width, stop);
            }
            else {
                ctx.lineTo(sleft, stop + height);
            }
            ctx.stroke();
            ctx.restore();
        }
    }
}
exports.SpanView = SpanView;
SpanView.__name__ = "SpanView";
class Span extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Span() {
        this.prototype.default_view = SpanView;
        this.mixins(['line']);
        this.define({
            render_mode: [p.RenderMode, 'canvas'],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
            location: [p.Number, null],
            location_units: [p.SpatialUnits, 'data'],
            dimension: [p.Dimension, 'width'],
        });
        this.override({
            line_color: 'black',
        });
        this.internal({
            for_hover: [p.Boolean, false],
            computed_location: [p.Number, null],
        });
    }
}
exports.Span = Span;
Span.__name__ = "Span";
Span.init_Span();
