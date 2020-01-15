"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const has_props_1 = require("./has_props");
const selection_1 = require("../models/selections/selection");
const glyph_renderer_1 = require("../models/renderers/glyph_renderer");
const graph_renderer_1 = require("../models/renderers/graph_renderer");
const p = require("./properties");
class SelectionManager extends has_props_1.HasProps {
    constructor(attrs) {
        super(attrs);
        this.inspectors = {};
    }
    static init_SelectionManager() {
        this.internal({
            source: [p.Any],
        });
    }
    select(renderer_views, geometry, final, append = false) {
        // divide renderers into glyph_renderers or graph_renderers
        const glyph_renderer_views = [];
        const graph_renderer_views = [];
        for (const r of renderer_views) {
            if (r instanceof glyph_renderer_1.GlyphRendererView)
                glyph_renderer_views.push(r);
            else if (r instanceof graph_renderer_1.GraphRendererView)
                graph_renderer_views.push(r);
        }
        let did_hit = false;
        // graph renderer case
        for (const r of graph_renderer_views) {
            const hit_test_result = r.model.selection_policy.hit_test(geometry, r);
            did_hit = did_hit || r.model.selection_policy.do_selection(hit_test_result, r.model, final, append);
        }
        // glyph renderers
        if (glyph_renderer_views.length > 0) {
            const hit_test_result = this.source.selection_policy.hit_test(geometry, glyph_renderer_views);
            did_hit = did_hit || this.source.selection_policy.do_selection(hit_test_result, this.source, final, append);
        }
        return did_hit;
    }
    inspect(renderer_view, geometry) {
        let did_hit = false;
        if (renderer_view instanceof glyph_renderer_1.GlyphRendererView) {
            const hit_test_result = renderer_view.hit_test(geometry);
            if (hit_test_result != null) {
                did_hit = !hit_test_result.is_empty();
                const inspection = this.get_or_create_inspector(renderer_view.model);
                inspection.update(hit_test_result, true, false);
                this.source.setv({ inspected: inspection }, { silent: true });
                this.source.inspect.emit([renderer_view, { geometry }]);
            }
        }
        else if (renderer_view instanceof graph_renderer_1.GraphRendererView) {
            const hit_test_result = renderer_view.model.inspection_policy.hit_test(geometry, renderer_view);
            did_hit = did_hit || renderer_view.model.inspection_policy.do_inspection(hit_test_result, geometry, renderer_view, false, false);
        }
        return did_hit;
    }
    clear(rview) {
        this.source.selected.clear();
        if (rview != null)
            this.get_or_create_inspector(rview.model).clear();
    }
    get_or_create_inspector(rmodel) {
        if (this.inspectors[rmodel.id] == null)
            this.inspectors[rmodel.id] = new selection_1.Selection();
        return this.inspectors[rmodel.id];
    }
}
exports.SelectionManager = SelectionManager;
SelectionManager.__name__ = "SelectionManager";
SelectionManager.init_SelectionManager();
