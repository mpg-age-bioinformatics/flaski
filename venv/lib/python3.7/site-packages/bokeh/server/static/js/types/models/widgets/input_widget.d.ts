import { Control, ControlView } from "./control";
import { CallbackLike0 } from "../callbacks/callback";
import * as p from "../../core/properties";
export declare abstract class InputWidgetView extends ControlView {
    model: InputWidget;
    protected label_el: HTMLLabelElement;
    protected group_el: HTMLElement;
    connect_signals(): void;
    render(): void;
    change_input(): void;
}
export declare namespace InputWidget {
    type Attrs = p.AttrsOf<Props>;
    type Props = Control.Props & {
        title: p.Property<string>;
        callback: p.Property<CallbackLike0<InputWidget> | null>;
    };
}
export interface InputWidget extends InputWidget.Attrs {
}
export declare abstract class InputWidget extends Control {
    properties: InputWidget.Props;
    constructor(attrs?: Partial<InputWidget.Attrs>);
    static init_InputWidget(): void;
}
