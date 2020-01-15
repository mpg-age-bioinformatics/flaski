import { InputWidget, InputWidgetView } from "./input_widget";
import * as p from "../../core/properties";
import "../../styles/widgets/pikaday";
export declare class DatePickerView extends InputWidgetView {
    model: DatePicker;
    protected input_el: HTMLInputElement;
    private _picker;
    connect_signals(): void;
    render(): void;
    _unlocal_date(date: Date): Date;
    _on_select(date: Date): void;
}
export declare namespace DatePicker {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputWidget.Props & {
        value: p.Property<string>;
        min_date: p.Property<string>;
        max_date: p.Property<string>;
    };
}
export interface DatePicker extends DatePicker.Attrs {
}
export declare class DatePicker extends InputWidget {
    properties: DatePicker.Props;
    constructor(attrs?: Partial<DatePicker.Attrs>);
    static init_DatePicker(): void;
}
