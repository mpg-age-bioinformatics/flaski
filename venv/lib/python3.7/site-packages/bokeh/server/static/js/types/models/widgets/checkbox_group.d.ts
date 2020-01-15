import { InputGroup, InputGroupView } from "./input_group";
import { CallbackLike0 } from "../callbacks/callback";
import * as p from "../../core/properties";
export declare class CheckboxGroupView extends InputGroupView {
    model: CheckboxGroup;
    render(): void;
    change_active(i: number): void;
}
export declare namespace CheckboxGroup {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputGroup.Props & {
        active: p.Property<number[]>;
        labels: p.Property<string[]>;
        inline: p.Property<boolean>;
        callback: p.Property<CallbackLike0<CheckboxGroup> | null>;
    };
}
export interface CheckboxGroup extends CheckboxGroup.Attrs {
}
export declare class CheckboxGroup extends InputGroup {
    properties: CheckboxGroup.Props;
    constructor(attrs?: Partial<CheckboxGroup.Attrs>);
    static init_CheckboxGroup(): void;
}
