import { LayoutProvider } from "./layout_provider";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import * as p from "../../core/properties";
export declare namespace StaticLayoutProvider {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutProvider.Props & {
        graph_layout: p.Property<{
            [key: string]: [number, number];
        }>;
    };
}
export interface StaticLayoutProvider extends StaticLayoutProvider.Attrs {
}
export declare class StaticLayoutProvider extends LayoutProvider {
    properties: StaticLayoutProvider.Props;
    constructor(attrs?: Partial<StaticLayoutProvider.Attrs>);
    static init_StaticLayoutProvider(): void;
    get_node_coordinates(node_source: ColumnarDataSource): [number[], number[]];
    get_edge_coordinates(edge_source: ColumnarDataSource): [[number, number][], [number, number][]];
}
