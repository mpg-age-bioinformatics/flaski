import { LayoutDOM, LayoutDOMView } from "../layouts/layout_dom";
import * as p from "../../core/properties";
export declare namespace HTMLBoxView {
    type Options = LayoutDOMView.Options & {
        model: HTMLBox;
    };
}
export declare abstract class HTMLBoxView extends LayoutDOMView {
    model: HTMLBox;
    readonly child_models: LayoutDOM[];
    _update_layout(): void;
}
export declare namespace HTMLBox {
    type Attrs = p.AttrsOf<Props>;
    type Props = LayoutDOM.Props;
}
export declare abstract class HTMLBox extends LayoutDOM {
    properties: HTMLBox.Props;
    constructor(attrs?: Partial<HTMLBox.Attrs>);
}
