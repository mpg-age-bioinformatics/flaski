import * as p from "../../core/properties";
import { ButtonType } from "../../core/enums";
import { Control, ControlView } from "./control";
import { AbstractIcon, AbstractIconView } from "./abstract_icon";
import { CallbackLike0 } from "../callbacks/callback";
export declare abstract class AbstractButtonView extends ControlView {
    model: AbstractButton;
    protected icon_views: {
        [key: string]: AbstractIconView;
    };
    protected button_el: HTMLButtonElement;
    protected group_el: HTMLElement;
    initialize(): void;
    connect_signals(): void;
    remove(): void;
    _render_button(...children: (string | HTMLElement)[]): HTMLButtonElement;
    render(): void;
    click(): void;
}
export declare namespace AbstractButton {
    type Attrs = p.AttrsOf<Props>;
    type Props = Control.Props & {
        label: p.Property<string>;
        icon: p.Property<AbstractIcon>;
        button_type: p.Property<ButtonType>;
        callback: p.Property<CallbackLike0<AbstractButton> | null>;
    };
}
export interface AbstractButton extends AbstractButton.Attrs {
}
export declare abstract class AbstractButton extends Control {
    properties: AbstractButton.Props;
    constructor(attrs?: Partial<AbstractButton.Attrs>);
    static init_AbstractButton(): void;
}
