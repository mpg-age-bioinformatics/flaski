"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const select_tool_1 = require("./select_tool");
const poly_annotation_1 = require("../../annotations/poly_annotation");
const dom_1 = require("../../../core/dom");
const p = require("../../../core/properties");
const array_1 = require("../../../core/util/array");
const icons_1 = require("../../../styles/icons");
class PolySelectToolView extends select_tool_1.SelectToolView {
    initialize() {
        super.initialize();
        this.data = { sx: [], sy: [] };
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.active.change, () => this._active_change());
    }
    _active_change() {
        if (!this.model.active)
            this._clear_data();
    }
    _keyup(ev) {
        if (ev.keyCode == dom_1.Keys.Enter)
            this._clear_data();
    }
    _doubletap(ev) {
        const append = ev.shiftKey;
        this._do_select(this.data.sx, this.data.sy, true, append);
        this.plot_view.push_state('poly_select', { selection: this.plot_view.get_selection() });
        this._clear_data();
    }
    _clear_data() {
        this.data = { sx: [], sy: [] };
        this.model.overlay.update({ xs: [], ys: [] });
    }
    _tap(ev) {
        const { sx, sy } = ev;
        const frame = this.plot_view.frame;
        if (!frame.bbox.contains(sx, sy))
            return;
        this.data.sx.push(sx);
        this.data.sy.push(sy);
        this.model.overlay.update({ xs: array_1.copy(this.data.sx), ys: array_1.copy(this.data.sy) });
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
exports.PolySelectToolView = PolySelectToolView;
PolySelectToolView.__name__ = "PolySelectToolView";
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
class PolySelectTool extends select_tool_1.SelectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Poly Select";
        this.icon = icons_1.bk_tool_icon_polygon_select;
        this.event_type = "tap";
        this.default_order = 11;
    }
    static init_PolySelectTool() {
        this.prototype.default_view = PolySelectToolView;
        this.define({
            callback: [p.Any],
            overlay: [p.Instance, DEFAULT_POLY_OVERLAY],
        });
    }
}
exports.PolySelectTool = PolySelectTool;
PolySelectTool.__name__ = "PolySelectTool";
PolySelectTool.init_PolySelectTool();
