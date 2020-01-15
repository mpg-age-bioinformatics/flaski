import { Control, ControlView } from "./control";
import { CallbackLike0 } from "../callbacks/callback";
import { ButtonType } from "../../core/enums";
import * as p from "../../core/properties";
export declare abstract class ButtonGroupView extends ControlView {
    model: ButtonGroup;
    protected _buttons: HTMLElement[];
    connect_signals(): void;
    render(): void;
    abstract change_active(i: number): void;
    protected abstract _update_active(): void;
}
export declare namespace ButtonGroup {
    type Attrs = p.AttrsOf<Props>;
    type Props = Control.Props & {
        labels: p.Property<string[]>;
        button_type: p.Property<ButtonType>;
        callback: p.Property<CallbackLike0<ButtonGroup> | null>;
    };
}
export interface ButtonGroup extends ButtonGroup.Attrs {
}
export declare abstract class ButtonGroup extends Control {
    properties: ButtonGroup.Props & {
        active: p.Property<unknown>;
    };
    constructor(attrs?: Partial<ButtonGroup.Attrs>);
    static init_ButtonGroup(): void;
}
