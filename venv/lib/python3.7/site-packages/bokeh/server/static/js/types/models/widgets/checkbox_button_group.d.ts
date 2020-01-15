import { ButtonGroup, ButtonGroupView } from "./button_group";
import { Class } from "../../core/class";
import { Set } from "../../core/util/data_structures";
import * as p from "../../core/properties";
export declare class CheckboxButtonGroupView extends ButtonGroupView {
    model: CheckboxButtonGroup;
    readonly active: Set<number>;
    change_active(i: number): void;
    protected _update_active(): void;
}
export declare namespace CheckboxButtonGroup {
    type Attrs = p.AttrsOf<Props>;
    type Props = ButtonGroup.Props & {
        active: p.Property<number[]>;
    };
}
export interface CheckboxButtonGroup extends CheckboxButtonGroup.Attrs {
}
export declare class CheckboxButtonGroup extends ButtonGroup {
    properties: CheckboxButtonGroup.Props;
    default_view: Class<CheckboxButtonGroupView>;
    constructor(attrs?: Partial<CheckboxButtonGroup.Attrs>);
    static init_CheckboxButtonGroup(): void;
}
