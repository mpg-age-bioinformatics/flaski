"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const data_renderer_1 = require("./data_renderer");
const graph_hit_test_policy_1 = require("../graphs/graph_hit_test_policy");
const p = require("../../core/properties");
const build_views_1 = require("../../core/build_views");
class GraphRendererView extends data_renderer_1.DataRendererView {
    initialize() {
        super.initialize();
        this.xscale = this.plot_view.frame.xscales.default;
        this.yscale = this.plot_view.frame.yscales.default;
        this._renderer_views = {};
        [this.node_view, this.edge_view] = build_views_1.build_views(this._renderer_views, [
            this.model.node_renderer,
            this.model.edge_renderer,
        ], { parent: this.parent });
        this.set_data();
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.layout_provider.change, () => this.set_data());
        this.connect(this.model.node_renderer.data_source._select, () => this.set_data());
        this.connect(this.model.node_renderer.data_source.inspect, () => this.set_data());
        this.connect(this.model.node_renderer.data_source.change, () => this.set_data());
        this.connect(this.model.edge_renderer.data_source._select, () => this.set_data());
        this.connect(this.model.edge_renderer.data_source.inspect, () => this.set_data());
        this.connect(this.model.edge_renderer.data_source.change, () => this.set_data());
        const { x_ranges, y_ranges } = this.plot_view.frame;
        for (const name in x_ranges) {
            const rng = x_ranges[name];
            this.connect(rng.change, () => this.set_data());
        }
        for (const name in y_ranges) {
            const rng = y_ranges[name];
            this.connect(rng.change, () => this.set_data());
        }
    }
    set_data(request_render = true) {
        // TODO (bev) this is a bit clunky, need to make sure glyphs use the correct ranges when they call
        // mapping functions on the base Renderer class
        this.node_view.glyph.model.setv({ x_range_name: this.model.x_range_name, y_range_name: this.model.y_range_name }, { silent: true });
        this.edge_view.glyph.model.setv({ x_range_name: this.model.x_range_name, y_range_name: this.model.y_range_name }, { silent: true });
        // XXX
        const node_glyph = this.node_view.glyph;
        [node_glyph._x, node_glyph._y] =
            this.model.layout_provider.get_node_coordinates(this.model.node_renderer.data_source);
        const edge_glyph = this.edge_view.glyph;
        [edge_glyph._xs, edge_glyph._ys] =
            this.model.layout_provider.get_edge_coordinates(this.model.edge_renderer.data_source);
        node_glyph.index_data();
        edge_glyph.index_data();
        if (request_render)
            this.request_render();
    }
    render() {
        this.edge_view.render();
        this.node_view.render();
    }
}
exports.GraphRendererView = GraphRendererView;
GraphRendererView.__name__ = "GraphRendererView";
class GraphRenderer extends data_renderer_1.DataRenderer {
    constructor(attrs) {
        super(attrs);
    }
    static init_GraphRenderer() {
        this.prototype.default_view = GraphRendererView;
        this.define({
            layout_provider: [p.Instance],
            node_renderer: [p.Instance],
            edge_renderer: [p.Instance],
            selection_policy: [p.Instance, () => new graph_hit_test_policy_1.NodesOnly()],
            inspection_policy: [p.Instance, () => new graph_hit_test_policy_1.NodesOnly()],
        });
    }
    get_selection_manager() {
        return this.node_renderer.data_source.selection_manager;
    }
}
exports.GraphRenderer = GraphRenderer;
GraphRenderer.__name__ = "GraphRenderer";
GraphRenderer.init_GraphRenderer();
