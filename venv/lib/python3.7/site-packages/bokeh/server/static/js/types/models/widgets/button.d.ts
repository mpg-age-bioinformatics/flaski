import { AbstractButton, AbstractButtonView } from "./abstract_button";
import * as p from "../../core/properties";
export declare class ButtonView extends AbstractButtonView {
    model: Button;
    click(): void;
}
export declare namespace Button {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractButton.Props & {
        clicks: p.Property<number>;
    };
}
export interface Button extends Button.Attrs {
}
export declare class Button extends AbstractButton {
    properties: Button.Props;
    constructor(attrs?: Partial<Button.Attrs>);
    static init_Button(): void;
}
