"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const select_tool_1 = require("./select_tool");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class TapToolView extends select_tool_1.SelectToolView {
    _tap(ev) {
        const { sx, sy } = ev;
        const geometry = { type: 'point', sx, sy };
        const append = ev.shiftKey;
        this._select(geometry, true, append);
    }
    _select(geometry, final, append) {
        const callback = this.model.callback;
        if (this.model.behavior == "select") {
            const renderers_by_source = this._computed_renderers_by_data_source();
            for (const id in renderers_by_source) {
                const renderers = renderers_by_source[id];
                const sm = renderers[0].get_selection_manager();
                const r_views = renderers.map((r) => this.plot_view.renderer_views[r.id]);
                const did_hit = sm.select(r_views, geometry, final, append);
                if (did_hit && callback != null) {
                    const { frame } = this.plot_view;
                    const xscale = frame.xscales[renderers[0].x_range_name];
                    const yscale = frame.yscales[renderers[0].y_range_name];
                    const x = xscale.invert(geometry.sx);
                    const y = yscale.invert(geometry.sy);
                    const data = { geometries: Object.assign(Object.assign({}, geometry), { x, y }), source: sm.source };
                    callback.execute(this.model, data);
                }
            }
            this._emit_selection_event(geometry);
            this.plot_view.push_state('tap', { selection: this.plot_view.get_selection() });
        }
        else {
            for (const r of this.computed_renderers) {
                const sm = r.get_selection_manager();
                const did_hit = sm.inspect(this.plot_view.renderer_views[r.id], geometry);
                if (did_hit && callback != null) {
                    const { frame } = this.plot_view;
                    const xscale = frame.xscales[r.x_range_name];
                    const yscale = frame.yscales[r.y_range_name];
                    const x = xscale.invert(geometry.sx);
                    const y = yscale.invert(geometry.sy);
                    const data = { geometries: Object.assign(Object.assign({}, geometry), { x, y }), source: sm.source };
                    callback.execute(this.model, data);
                }
            }
        }
    }
}
exports.TapToolView = TapToolView;
TapToolView.__name__ = "TapToolView";
class TapTool extends select_tool_1.SelectTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Tap";
        this.icon = icons_1.bk_tool_icon_tap_select;
        this.event_type = "tap";
        this.default_order = 10;
    }
    static init_TapTool() {
        this.prototype.default_view = TapToolView;
        this.define({
            behavior: [p.TapBehavior, "select"],
            callback: [p.Any],
        });
    }
}
exports.TapTool = TapTool;
TapTool.__name__ = "TapTool";
TapTool.init_TapTool();
