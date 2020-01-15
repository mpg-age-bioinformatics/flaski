import * as p from "../../core/properties";
import { InputGroup, InputGroupView } from "./input_group";
import { CallbackLike0 } from "../callbacks/callback";
export declare class RadioGroupView extends InputGroupView {
    model: RadioGroup;
    render(): void;
    change_active(i: number): void;
}
export declare namespace RadioGroup {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputGroup.Props & {
        active: p.Property<number>;
        labels: p.Property<string[]>;
        inline: p.Property<boolean>;
        callback: p.Property<CallbackLike0<RadioGroup> | null>;
    };
}
export interface RadioGroup extends RadioGroup.Attrs {
}
export declare class RadioGroup extends InputGroup {
    properties: RadioGroup.Props;
    constructor(attrs?: Partial<RadioGroup.Attrs>);
    static init_RadioGroup(): void;
}
