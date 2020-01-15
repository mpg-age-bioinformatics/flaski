import { Renderer, RendererView } from "./renderer";
import { SelectionManager } from "../../core/selection_manager";
import * as p from "../../core/properties";
export declare abstract class DataRendererView extends RendererView {
    model: DataRenderer;
    visuals: DataRenderer.Visuals;
}
export declare namespace DataRenderer {
    type Attrs = p.AttrsOf<Props>;
    type Props = Renderer.Props & {
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
    };
    type Visuals = Renderer.Visuals;
}
export interface DataRenderer extends DataRenderer.Attrs {
}
export declare abstract class DataRenderer extends Renderer {
    properties: DataRenderer.Props;
    constructor(attrs?: Partial<DataRenderer.Attrs>);
    static init_DataRenderer(): void;
    abstract get_selection_manager(): SelectionManager;
}
