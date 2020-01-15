"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const signaling_1 = require("../../core/signaling");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const bbox_1 = require("../../core/util/bbox");
const annotations_1 = require("../../styles/annotations");
exports.EDGE_TOLERANCE = 2.5;
class BoxAnnotationView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
        this.plot_view.canvas_overlays.appendChild(this.el);
        this.el.classList.add(annotations_1.bk_shading);
        dom_1.undisplay(this.el);
    }
    connect_signals() {
        super.connect_signals();
        // need to respond to either normal BB change events or silent
        // "data only updates" that tools might want to use
        if (this.model.render_mode == 'css') {
            // dispatch CSS update immediately
            this.connect(this.model.change, () => this.render());
            this.connect(this.model.data_update, () => this.render());
        }
        else {
            this.connect(this.model.change, () => this.plot_view.request_render());
            this.connect(this.model.data_update, () => this.plot_view.request_render());
        }
    }
    render() {
        if (!this.model.visible && this.model.render_mode == 'css')
            dom_1.undisplay(this.el);
        if (!this.model.visible)
            return;
        // don't render if *all* position are null
        if (this.model.left == null && this.model.right == null && this.model.top == null && this.model.bottom == null) {
            dom_1.undisplay(this.el);
            return;
        }
        const { frame } = this.plot_view;
        const xscale = frame.xscales[this.model.x_range_name];
        const yscale = frame.yscales[this.model.y_range_name];
        const _calc_dim = (dim, dim_units, scale, view, frame_extrema) => {
            let sdim;
            if (dim != null) {
                if (this.model.screen)
                    sdim = dim;
                else {
                    if (dim_units == 'data')
                        sdim = scale.compute(dim);
                    else
                        sdim = view.compute(dim);
                }
            }
            else
                sdim = frame_extrema;
            return sdim;
        };
        this.sleft = _calc_dim(this.model.left, this.model.left_units, xscale, frame.xview, frame._left.value);
        this.sright = _calc_dim(this.model.right, this.model.right_units, xscale, frame.xview, frame._right.value);
        this.stop = _calc_dim(this.model.top, this.model.top_units, yscale, frame.yview, frame._top.value);
        this.sbottom = _calc_dim(this.model.bottom, this.model.bottom_units, yscale, frame.yview, frame._bottom.value);
        const draw = this.model.render_mode == 'css' ? this._css_box.bind(this) : this._canvas_box.bind(this);
        draw(this.sleft, this.sright, this.sbottom, this.stop);
    }
    _css_box(sleft, sright, sbottom, stop) {
        const line_width = this.model.properties.line_width.value();
        const sw = Math.floor(sright - sleft) - line_width;
        const sh = Math.floor(sbottom - stop) - line_width;
        this.el.style.left = `${sleft}px`;
        this.el.style.width = `${sw}px`;
        this.el.style.top = `${stop}px`;
        this.el.style.height = `${sh}px`;
        this.el.style.borderWidth = `${line_width}px`;
        this.el.style.borderColor = this.model.properties.line_color.value();
        this.el.style.backgroundColor = this.model.properties.fill_color.value();
        this.el.style.opacity = this.model.properties.fill_alpha.value();
        // try our best to honor line dashing in some way, if we can
        const ld = this.model.properties.line_dash.value().length < 2 ? "solid" : "dashed";
        this.el.style.borderStyle = ld;
        dom_1.display(this.el);
    }
    _canvas_box(sleft, sright, sbottom, stop) {
        const { ctx } = this.plot_view.canvas_view;
        ctx.save();
        ctx.beginPath();
        ctx.rect(sleft, stop, sright - sleft, sbottom - stop);
        this.visuals.fill.set_value(ctx);
        ctx.fill();
        this.visuals.line.set_value(ctx);
        ctx.stroke();
        ctx.restore();
    }
    interactive_bbox() {
        const tol = this.model.properties.line_width.value() + exports.EDGE_TOLERANCE;
        return new bbox_1.BBox({
            x0: this.sleft - tol,
            y0: this.stop - tol,
            x1: this.sright + tol,
            y1: this.sbottom + tol,
        });
    }
    interactive_hit(sx, sy) {
        if (this.model.in_cursor == null)
            return false;
        const bbox = this.interactive_bbox();
        return bbox.contains(sx, sy);
    }
    cursor(sx, sy) {
        const tol = 3;
        if (Math.abs(sx - this.sleft) < tol || Math.abs(sx - this.sright) < tol)
            return this.model.ew_cursor;
        else if (Math.abs(sy - this.sbottom) < tol || Math.abs(sy - this.stop) < tol)
            return this.model.ns_cursor;
        else if (sx > this.sleft && sx < this.sright && sy > this.stop && sy < this.sbottom)
            return this.model.in_cursor;
        else
            return null;
    }
}
exports.BoxAnnotationView = BoxAnnotationView;
BoxAnnotationView.__name__ = "BoxAnnotationView";
class BoxAnnotation extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_BoxAnnotation() {
        this.prototype.default_view = BoxAnnotationView;
        this.mixins(['line', 'fill']);
        this.define({
            render_mode: [p.RenderMode, 'canvas'],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
            top: [p.Number, null],
            top_units: [p.SpatialUnits, 'data'],
            bottom: [p.Number, null],
            bottom_units: [p.SpatialUnits, 'data'],
            left: [p.Number, null],
            left_units: [p.SpatialUnits, 'data'],
            right: [p.Number, null],
            right_units: [p.SpatialUnits, 'data'],
        });
        this.internal({
            screen: [p.Boolean, false],
            ew_cursor: [p.String, null],
            ns_cursor: [p.String, null],
            in_cursor: [p.String, null],
        });
        this.override({
            fill_color: '#fff9ba',
            fill_alpha: 0.4,
            line_color: '#cccccc',
            line_alpha: 0.3,
        });
    }
    initialize() {
        super.initialize();
        this.data_update = new signaling_1.Signal0(this, "data_update");
    }
    update({ left, right, top, bottom }) {
        this.setv({ left, right, top, bottom, screen: true }, { silent: true });
        this.data_update.emit();
    }
}
exports.BoxAnnotation = BoxAnnotation;
BoxAnnotation.__name__ = "BoxAnnotation";
BoxAnnotation.init_BoxAnnotation();
