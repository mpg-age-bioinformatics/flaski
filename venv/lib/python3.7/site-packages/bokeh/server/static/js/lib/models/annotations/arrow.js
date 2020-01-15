"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const arrow_head_1 = require("./arrow_head");
const column_data_source_1 = require("../sources/column_data_source");
const p = require("../../core/properties");
const math_1 = require("../../core/util/math");
class ArrowView extends annotation_1.AnnotationView {
    initialize() {
        super.initialize();
        if (this.model.source == null)
            this.model.source = new column_data_source_1.ColumnDataSource();
        this.set_data(this.model.source);
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.set_data(this.model.source));
        this.connect(this.model.source.streaming, () => this.set_data(this.model.source));
        this.connect(this.model.source.patching, () => this.set_data(this.model.source));
    }
    set_data(source) {
        super.set_data(source);
        this.visuals.warm_cache(source);
        this.plot_view.request_render();
    }
    _map_data() {
        const { frame } = this.plot_view;
        let sx_start, sy_start;
        if (this.model.start_units == 'data') {
            sx_start = frame.xscales[this.model.x_range_name].v_compute(this._x_start);
            sy_start = frame.yscales[this.model.y_range_name].v_compute(this._y_start);
        }
        else {
            sx_start = frame.xview.v_compute(this._x_start);
            sy_start = frame.yview.v_compute(this._y_start);
        }
        let sx_end, sy_end;
        if (this.model.end_units == 'data') {
            sx_end = frame.xscales[this.model.x_range_name].v_compute(this._x_end);
            sy_end = frame.yscales[this.model.y_range_name].v_compute(this._y_end);
        }
        else {
            sx_end = frame.xview.v_compute(this._x_end);
            sy_end = frame.yview.v_compute(this._y_end);
        }
        return [[sx_start, sy_start], [sx_end, sy_end]];
    }
    render() {
        if (!this.model.visible)
            return;
        const { ctx } = this.plot_view.canvas_view;
        ctx.save();
        // Order in this function is important. First we draw all the arrow heads.
        const [start, end] = this._map_data();
        if (this.model.end != null)
            this._arrow_head(ctx, "render", this.model.end, start, end);
        if (this.model.start != null)
            this._arrow_head(ctx, "render", this.model.start, end, start);
        // Next we call .clip on all the arrow heads, inside an initial canvas sized
        // rect, to create an "inverted" clip region for the arrow heads
        ctx.beginPath();
        const { x, y, width, height } = this.plot_view.layout.bbox;
        ctx.rect(x, y, width, height);
        if (this.model.end != null)
            this._arrow_head(ctx, "clip", this.model.end, start, end);
        if (this.model.start != null)
            this._arrow_head(ctx, "clip", this.model.start, end, start);
        ctx.closePath();
        ctx.clip();
        // Finally we draw the arrow body, with the clipping regions set up. This prevents
        // "fat" arrows from overlapping the arrow head in a bad way.
        this._arrow_body(ctx, start, end);
        ctx.restore();
    }
    _arrow_head(ctx, action, head, start, end) {
        for (let i = 0, _end = this._x_start.length; i < _end; i++) {
            // arrow head runs orthogonal to arrow body
            const angle = Math.PI / 2 + math_1.atan2([start[0][i], start[1][i]], [end[0][i], end[1][i]]);
            ctx.save();
            ctx.translate(end[0][i], end[1][i]);
            ctx.rotate(angle);
            if (action == "render")
                head.render(ctx, i);
            else if (action == "clip")
                head.clip(ctx, i);
            ctx.restore();
        }
    }
    _arrow_body(ctx, start, end) {
        if (!this.visuals.line.doit)
            return;
        for (let i = 0, n = this._x_start.length; i < n; i++) {
            this.visuals.line.set_vectorize(ctx, i);
            ctx.beginPath();
            ctx.moveTo(start[0][i], start[1][i]);
            ctx.lineTo(end[0][i], end[1][i]);
            ctx.stroke();
        }
    }
}
exports.ArrowView = ArrowView;
ArrowView.__name__ = "ArrowView";
class Arrow extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_Arrow() {
        this.prototype.default_view = ArrowView;
        this.mixins(['line']);
        this.define({
            x_start: [p.NumberSpec],
            y_start: [p.NumberSpec],
            start_units: [p.SpatialUnits, 'data'],
            start: [p.Instance, null],
            x_end: [p.NumberSpec],
            y_end: [p.NumberSpec],
            end_units: [p.SpatialUnits, 'data'],
            end: [p.Instance, () => new arrow_head_1.OpenHead({})],
            source: [p.Instance],
            x_range_name: [p.String, 'default'],
            y_range_name: [p.String, 'default'],
        });
    }
}
exports.Arrow = Arrow;
Arrow.__name__ = "Arrow";
Arrow.init_Arrow();
