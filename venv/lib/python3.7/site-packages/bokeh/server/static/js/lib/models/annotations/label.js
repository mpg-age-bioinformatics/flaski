"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const text_annotation_1 = require("./text_annotation");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
class LabelView extends text_annotation_1.TextAnnotationView {
    initialize() {
        super.initialize();
        this.visuals.warm_cache();
    }
    _get_size() {
        const { ctx } = this.plot_view.canvas_view;
        this.visuals.text.set_value(ctx);
        const { width, ascent } = ctx.measureText(this.model.text);
        return { width, height: ascent };
    }
    render() {
        if (!this.model.visible && this.model.render_mode == 'css')
            dom_1.undisplay(this.el);
        if (!this.model.visible)
            return;
        // Here because AngleSpec does units transform and label doesn't support specs
        let angle;
        switch (this.model.angle_units) {
            case "rad": {
                angle = -this.model.angle;
                break;
            }
            case "deg": {
                angle = (-this.model.angle * Math.PI) / 180.0;
                break;
            }
            default:
                throw new Error("unreachable code");
        }
        const panel = this.panel != null ? this.panel : this.plot_view.frame;
        const xscale = this.plot_view.frame.xscales[this.model.x_range_name];
        const yscale = this.plot_view.frame.yscales[this.model.y_range_name];
        let sx = this.model.x_units == "data" ? xscale.compute(this.model.x) : panel.xview.compute(this.model.x);
        let sy = this.model.y_units == "data" ? yscale.compute(this.model.y) : panel.yview.compute(this.model.y);
        sx += this.model.x_offset;
        sy -= this.model.y_offset;
        const draw = this.model.render_mode == 'canvas' ? this._canvas_text.bind(this) : this._css_text.bind(this);
        draw(this.plot_view.canvas_view.ctx, this.model.text, sx, sy, angle);
    }
}
exports.LabelView = LabelView;
LabelView.__name__ = "LabelView";
class Label extends text_annotation_1.TextAnnotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Label() {
        this.prototype.default_view = LabelView;
        this.mixins(['text', 'line:border_', 'fill:background_']);
        this.define({
            x: [p.Number],
            x_units: [p.SpatialUnits, 'data'],
            y: [p.Number],
            y_units: [p.SpatialUnits, 'data'],
            text: [p.String],
            angle: [p.Angle, 0],
            angle_units: [p.AngleUnits, 'rad'],
            x_offset: [p.Number, 0],
            y_offset: [p.Number, 0],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
        this.override({
            background_fill_color: null,
            border_line_color: null,
        });
    }
}
exports.Label = Label;
Label.__name__ = "Label";
Label.init_Label();
