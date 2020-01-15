"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const select_tool_1 = require("./select_tool");
const poly_annotation_1 = require("../../annotations/poly_annotation");
const dom_1 = require("../../../core/dom");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class LassoSelectToolView extends select_tool_1.SelectToolView {
    initialize() {
        super.initialize();
        this.data = null;
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.active.change, () => this._active_change());
    }
    _active_change() {
        if (!this.model.active)
            this._clear_overlay();
    }
    _keyup(ev) {
        if (ev.keyCode == dom_1.Keys.Enter)
            this._clear_overlay();
    }
    _pan_start(ev) {
        const { sx, sy } = ev;
        this.data = { sx: [sx], sy: [sy] };
    }
    _pan(ev) {
        const { sx: _sx, sy: _sy } = ev;
        const [sx, sy] = this.plot_view.frame.bbox.clip(_sx, _sy);
        this.data.sx.push(sx);
        this.data.sy.push(sy);
        const overlay = this.model.overlay;
        overlay.update({ xs: this.data.sx, ys: this.data.sy });
        if (this.model.select_every_mousemove) {
            const append = ev.shiftKey;
            this._do_select(this.data.sx, this.data.sy, false, append);
        }
    }
    _pan_end(ev) {
        this._clear_overlay();
        const append = ev.shiftKey;
        this._do_select(this.data.sx, this.data.sy, true, append);
        this.plot_view.push_state('lasso_select', { selection: this.plot_view.get_selection() });
    }
    _clear_overlay() {
        this.model.overlay.update({ xs: [], ys: [] });
    }
    _do_select(sx, sy, final, append) {
        const geometry = { type: 'poly', sx, sy };
        this._select(geometry, final, append);
    }
    _emit_callback(geometry) {
        const r = this.computed_renderers[0];
        const frame = this.plot_view.frame;
        const xscale = frame.xscales[r.x_range_name];
        const yscale = frame.yscales[r.y_range_name];
        const x = xscale.v_invert(geometry.sx);
        const y = yscale.v_invert(geometry.sy);
        const g = Object.assign({ x, y }, geometry);
        if (this.model.callback != null)
            this.model.callback.execute(this.model, { geometry: g });
    }
}
exports.LassoSelectToolView = LassoSelectToolView;
LassoSelectToolView.__name__ = "LassoSelectToolView";
const DEFAULT_POLY_OVERLAY = () => {
    return new poly_annotation_1.PolyAnnotation({
        level: "overlay",
        xs_units: "screen",
        ys_units: "screen",
        fill_color: { value: "lightgrey" },
        fill_alpha: { value: 0.5 },
        line_color: { value: "black" },
        line_alpha: { value: 1.0 },
        line_width: { value: 2 },
        line_dash: { value: [4, 4] },
    });
};
class LassoSelectTool extends select_tool_1.SelectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Lasso Select";
        this.icon = icons_1.bk_tool_icon_lasso_select;
        this.event_type = "pan";
        this.default_order = 12;
    }
    static init_LassoSelectTool() {
        this.prototype.default_view = LassoSelectToolView;
        this.define({
            select_every_mousemove: [p.Boolean, true],
            callback: [p.Any],
            overlay: [p.Instance, DEFAULT_POLY_OVERLAY],
        });
    }
}
exports.LassoSelectTool = LassoSelectTool;
LassoSelectTool.__name__ = "LassoSelectTool";
LassoSelectTool.init_LassoSelectTool();
