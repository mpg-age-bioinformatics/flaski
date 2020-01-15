import { LayoutDOM, LayoutDOMView } from "./layout_dom";
import * as p from "../../core/properties";
export declare class SpacerView extends LayoutDOMView {
    model: Spacer;
    readonly child_models: LayoutDOM[];
    _update_layout(): void;
}
export declare namespace Spacer {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutDOM.Props;
}
export interface Spacer extends Spacer.Attrs {
}
export declare class Spacer extends LayoutDOM {
    properties: Spacer.Props;
    constructor(attrs?: Partial<Spacer.Attrs>);
    static init_Spacer(): void;
}
