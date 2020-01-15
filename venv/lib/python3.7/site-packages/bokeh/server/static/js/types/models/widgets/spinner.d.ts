import { InputWidget, InputWidgetView } from "./input_widget";
import * as p from "../../core/properties";
export declare class SpinnerView extends InputWidgetView {
    model: Spinner;
    protected input_el: HTMLInputElement;
    connect_signals(): void;
    render(): void;
    change_input(): void;
}
export declare namespace Spinner {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputWidget.Props & {
        value: p.Property<number>;
        low: p.Property<number | null>;
        high: p.Property<number | null>;
        step: p.Property<number>;
    };
}
export interface Spinner extends Spinner.Attrs {
}
export declare class Spinner extends InputWidget {
    properties: Spinner.Props;
    constructor(attrs?: Partial<Spinner.Attrs>);
    static init_Spinner(): void;
}
