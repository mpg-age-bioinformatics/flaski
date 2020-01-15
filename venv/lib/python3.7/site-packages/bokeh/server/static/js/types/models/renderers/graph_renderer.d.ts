import { DataRenderer, DataRendererView } from "./data_renderer";
import { GlyphRenderer, GlyphRendererView } from "./glyph_renderer";
import { LayoutProvider } from "../graphs/layout_provider";
import { GraphHitTestPolicy } from "../graphs/graph_hit_test_policy";
import { Scale } from "../scales/scale";
import * as p from "../../core/properties";
import { SelectionManager } from "../../core/selection_manager";
export declare class GraphRendererView extends DataRendererView {
    model: GraphRenderer;
    node_view: GlyphRendererView;
    edge_view: GlyphRendererView;
    xscale: Scale;
    yscale: Scale;
    protected _renderer_views: {
        [key: string]: GlyphRendererView;
    };
    initialize(): void;
    connect_signals(): void;
    set_data(request_render?: boolean): void;
    render(): void;
}
export declare namespace GraphRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = DataRenderer.Props & {
        layout_provider: p.Property<LayoutProvider>;
        node_renderer: p.Property<GlyphRenderer>;
        edge_renderer: p.Property<GlyphRenderer>;
        selection_policy: p.Property<GraphHitTestPolicy>;
        inspection_policy: p.Property<GraphHitTestPolicy>;
    };
}
export interface GraphRenderer extends GraphRenderer.Attrs {
}
export declare class GraphRenderer extends DataRenderer {
    properties: GraphRenderer.Props;
    constructor(attrs?: Partial<GraphRenderer.Attrs>);
    static init_GraphRenderer(): void;
    get_selection_manager(): SelectionManager;
}
