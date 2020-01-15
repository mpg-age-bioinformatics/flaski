import { Widget, WidgetView } from "./widget";
import * as p from "../../core/properties";
export declare abstract class ControlView extends WidgetView {
    model: Control;
    connect_signals(): void;
}
export declare namespace Control {
    type Attrs = p.AttrsOf<Props>;
    type Props = Widget.Props;
}
export interface Control extends Control.Attrs {
}
export declare abstract class Control extends Widget {
    properties: Control.Props;
    constructor(attrs?: Partial<Control.Attrs>);
}
