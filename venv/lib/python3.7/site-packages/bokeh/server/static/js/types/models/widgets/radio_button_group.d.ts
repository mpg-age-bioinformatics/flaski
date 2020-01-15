import { ButtonGroup, ButtonGroupView } from "./button_group";
import { Class } from "../../core/class";
import * as p from "../../core/properties";
export declare class RadioButtonGroupView extends ButtonGroupView {
    model: RadioButtonGroup;
    change_active(i: number): void;
    protected _update_active(): void;
}
export declare namespace RadioButtonGroup {
    type Attrs = p.AttrsOf<Props>;
    type Props = ButtonGroup.Props & {
        active: p.Property<number | null>;
    };
}
export interface RadioButtonGroup extends RadioButtonGroup.Attrs {
}
export declare class RadioButtonGroup extends ButtonGroup {
    properties: RadioButtonGroup.Props;
    default_view: Class<RadioButtonGroupView>;
    constructor(attrs?: Partial<RadioButtonGroup.Attrs>);
    static init_RadioButtonGroup(): void;
}
