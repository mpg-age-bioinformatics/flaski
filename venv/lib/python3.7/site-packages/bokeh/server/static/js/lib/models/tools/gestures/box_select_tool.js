"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const select_tool_1 = require("./select_tool");
const box_annotation_1 = require("../../annotations/box_annotation");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class BoxSelectToolView extends select_tool_1.SelectToolView {
    _compute_limits(curpoint) {
        const frame = this.plot_view.frame;
        const dims = this.model.dimensions;
        let base_point = this._base_point;
        if (this.model.origin == "center") {
            const [cx, cy] = base_point;
            const [dx, dy] = curpoint;
            base_point = [cx - (dx - cx), cy - (dy - cy)];
        }
        return this.model._get_dim_limits(base_point, curpoint, frame, dims);
    }
    _pan_start(ev) {
        const { sx, sy } = ev;
        this._base_point = [sx, sy];
    }
    _pan(ev) {
        const { sx, sy } = ev;
        const curpoint = [sx, sy];
        const [sxlim, sylim] = this._compute_limits(curpoint);
        this.model.overlay.update({ left: sxlim[0], right: sxlim[1], top: sylim[0], bottom: sylim[1] });
        if (this.model.select_every_mousemove) {
            const append = ev.shiftKey;
            this._do_select(sxlim, sylim, false, append);
        }
    }
    _pan_end(ev) {
        const { sx, sy } = ev;
        const curpoint = [sx, sy];
        const [sxlim, sylim] = this._compute_limits(curpoint);
        const append = ev.shiftKey;
        this._do_select(sxlim, sylim, true, append);
        this.model.overlay.update({ left: null, right: null, top: null, bottom: null });
        this._base_point = null;
        this.plot_view.push_state('box_select', { selection: this.plot_view.get_selection() });
    }
    _do_select([sx0, sx1], [sy0, sy1], final, append = false) {
        const geometry = { type: 'rect', sx0, sx1, sy0, sy1 };
        this._select(geometry, final, append);
    }
    _emit_callback(geometry) {
        const r = this.computed_renderers[0];
        const frame = this.plot_view.frame;
        const xscale = frame.xscales[r.x_range_name];
        const yscale = frame.yscales[r.y_range_name];
        const { sx0, sx1, sy0, sy1 } = geometry;
        const [x0, x1] = xscale.r_invert(sx0, sx1);
        const [y0, y1] = yscale.r_invert(sy0, sy1);
        const g = Object.assign({ x0, y0, x1, y1 }, geometry);
        if (this.model.callback != null)
            this.model.callback.execute(this.model, { geometry: g });
    }
}
exports.BoxSelectToolView = BoxSelectToolView;
BoxSelectToolView.__name__ = "BoxSelectToolView";
const DEFAULT_BOX_OVERLAY = () => {
    return new box_annotation_1.BoxAnnotation({
        level: "overlay",
        render_mode: "css",
        top_units: "screen",
        left_units: "screen",
        bottom_units: "screen",
        right_units: "screen",
        fill_color: { value: "lightgrey" },
        fill_alpha: { value: 0.5 },
        line_color: { value: "black" },
        line_alpha: { value: 1.0 },
        line_width: { value: 2 },
        line_dash: { value: [4, 4] },
    });
};
class BoxSelectTool extends select_tool_1.SelectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Box Select";
        this.icon = icons_1.bk_tool_icon_box_select;
        this.event_type = "pan";
        this.default_order = 30;
    }
    static init_BoxSelectTool() {
        this.prototype.default_view = BoxSelectToolView;
        this.define({
            dimensions: [p.Dimensions, "both"],
            select_every_mousemove: [p.Boolean, false],
            callback: [p.Any],
            overlay: [p.Instance, DEFAULT_BOX_OVERLAY],
            origin: [p.BoxOrigin, "corner"],
        });
    }
    get tooltip() {
        return this._get_dim_tooltip(this.tool_name, this.dimensions);
    }
}
exports.BoxSelectTool = BoxSelectTool;
BoxSelectTool.__name__ = "BoxSelectTool";
BoxSelectTool.init_BoxSelectTool();
