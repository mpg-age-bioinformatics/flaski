import { HasProps } from "./has_props";
import { Geometry } from "./geometry";
import { Selection } from "../models/selections/selection";
import { Renderer, RendererView } from "../models/renderers/renderer";
import * as p from "./properties";
import { ColumnarDataSource } from "../models/sources/columnar_data_source";
export declare namespace SelectionManager {
    type Props = HasProps.Props & {
        source: p.Property<ColumnarDataSource>;
    };
    type Attrs = p.AttrsOf<Props>;
}
export interface SelectionManager extends SelectionManager.Attrs {
}
export declare class SelectionManager extends HasProps {
    properties: SelectionManager.Props;
    constructor(attrs?: Partial<SelectionManager.Attrs>);
    static init_SelectionManager(): void;
    inspectors: {
        [key: string]: Selection;
    };
    select(renderer_views: RendererView[], geometry: Geometry, final: boolean, append?: boolean): boolean;
    inspect(renderer_view: RendererView, geometry: Geometry): boolean;
    clear(rview?: RendererView): void;
    get_or_create_inspector(rmodel: Renderer): Selection;
}
