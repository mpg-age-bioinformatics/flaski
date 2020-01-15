import { LayoutDOM, LayoutDOMView } from "./layout_dom";
import { Grid } from "../../core/layout";
import * as p from "../../core/properties";
export declare abstract class BoxView extends LayoutDOMView {
    model: Box;
    layout: Grid;
    connect_signals(): void;
    readonly child_models: LayoutDOM[];
}
export declare namespace Box {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutDOM.Props & {
        children: p.Property<LayoutDOM[]>;
        spacing: p.Property<number>;
    };
}
export interface Box extends Box.Attrs {
}
export declare abstract class Box extends LayoutDOM {
    properties: Box.Props;
    constructor(attrs?: Partial<Box.Attrs>);
    static init_Box(): void;
}
