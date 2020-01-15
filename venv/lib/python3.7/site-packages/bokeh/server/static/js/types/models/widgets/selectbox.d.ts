import * as p from "../../core/properties";
import { InputWidget, InputWidgetView } from "./input_widget";
export declare class SelectView extends InputWidgetView {
    model: Select;
    protected select_el: HTMLSelectElement;
    connect_signals(): void;
    build_options(values: (string | [string, string])[]): HTMLElement[];
    render(): void;
    change_input(): void;
}
export declare namespace Select {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputWidget.Props & {
        value: p.Property<string>;
        options: p.Property<(string | [string, string])[] | {
            [key: string]: (string | [string, string])[];
        }>;
    };
}
export interface Select extends Select.Attrs {
}
export declare class Select extends InputWidget {
    properties: Select.Props;
    constructor(attrs?: Partial<Select.Attrs>);
    static init_Select(): void;
}
