"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const gesture_tool_1 = require("./gesture_tool");
const glyph_renderer_1 = require("../../renderers/glyph_renderer");
const graph_renderer_1 = require("../../renderers/graph_renderer");
const util_1 = require("../util");
const p = require("../../../core/properties");
const dom_1 = require("../../../core/dom");
const bokeh_events_1 = require("../../../core/bokeh_events");
class SelectToolView extends gesture_tool_1.GestureToolView {
    get computed_renderers() {
        const renderers = this.model.renderers;
        const all_renderers = this.plot_model.renderers;
        const names = this.model.names;
        return util_1.compute_renderers(renderers, all_renderers, names);
    }
    _computed_renderers_by_data_source() {
        const renderers_by_source = {};
        for (const r of this.computed_renderers) {
            let source_id;
            if (r instanceof glyph_renderer_1.GlyphRenderer)
                source_id = r.data_source.id;
            else if (r instanceof graph_renderer_1.GraphRenderer)
                source_id = r.node_renderer.data_source.id;
            else
                continue;
            if (!(source_id in renderers_by_source))
                renderers_by_source[source_id] = [];
            renderers_by_source[source_id].push(r);
        }
        return renderers_by_source;
    }
    _keyup(ev) {
        if (ev.keyCode == dom_1.Keys.Esc) {
            for (const r of this.computed_renderers) {
                r.get_selection_manager().clear();
            }
            this.plot_view.request_render();
        }
    }
    _select(geometry, final, append) {
        const renderers_by_source = this._computed_renderers_by_data_source();
        for (const id in renderers_by_source) {
            const renderers = renderers_by_source[id];
            const sm = renderers[0].get_selection_manager();
            const r_views = [];
            for (const r of renderers) {
                if (r.id in this.plot_view.renderer_views)
                    r_views.push(this.plot_view.renderer_views[r.id]);
            }
            sm.select(r_views, geometry, final, append);
        }
        // XXX: messed up class structure
        if (this.model.callback != null)
            this._emit_callback(geometry);
        this._emit_selection_event(geometry, final);
    }
    _emit_selection_event(geometry, final = true) {
        const { frame } = this.plot_view;
        const xm = frame.xscales.default;
        const ym = frame.yscales.default;
        let g; // XXX: Geometry & something
        switch (geometry.type) {
            case 'point': {
                const { sx, sy } = geometry;
                const x = xm.invert(sx);
                const y = ym.invert(sy);
                g = Object.assign(Object.assign({}, geometry), { x, y });
                break;
            }
            case 'rect': {
                const { sx0, sx1, sy0, sy1 } = geometry;
                const [x0, x1] = xm.r_invert(sx0, sx1);
                const [y0, y1] = ym.r_invert(sy0, sy1);
                g = Object.assign(Object.assign({}, geometry), { x0, y0, x1, y1 });
                break;
            }
            case 'poly': {
                const { sx, sy } = geometry;
                const x = xm.v_invert(sx);
                const y = ym.v_invert(sy);
                g = Object.assign(Object.assign({}, geometry), { x, y });
                break;
            }
            default:
                throw new Error(`Unrecognized selection geometry type: '${geometry.type}'`);
        }
        this.plot_model.trigger_event(new bokeh_events_1.SelectionGeometry(g, final));
    }
}
exports.SelectToolView = SelectToolView;
SelectToolView.__name__ = "SelectToolView";
class SelectTool extends gesture_tool_1.GestureTool {
    constructor(attrs) {
        super(attrs);
    }
    static init_SelectTool() {
        this.define({
            renderers: [p.Any, 'auto'],
            names: [p.Array, []],
        });
    }
}
exports.SelectTool = SelectTool;
SelectTool.__name__ = "SelectTool";
SelectTool.init_SelectTool();
