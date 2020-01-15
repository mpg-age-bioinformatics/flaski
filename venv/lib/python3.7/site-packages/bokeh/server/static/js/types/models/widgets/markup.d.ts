import * as p from "../../core/properties";
import { Widget, WidgetView } from "./widget";
export declare abstract class MarkupView extends WidgetView {
    model: Markup;
    protected markup_el: HTMLElement;
    connect_signals(): void;
    _update_layout(): void;
    render(): void;
}
export declare namespace Markup {
    type Attrs = p.AttrsOf<Props>;
    type Props = Widget.Props & {
        text: p.Property<string>;
        style: p.Property<{
            [key: string]: string;
        }>;
    };
}
export interface Markup extends Markup.Attrs {
}
export declare abstract class Markup extends Widget {
    properties: Markup.Props;
    constructor(attrs?: Partial<Markup.Attrs>);
    static init_Markup(): void;
}
