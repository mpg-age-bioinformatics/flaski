import { InputWidget, InputWidgetView } from "./input_widget";
import { Color } from "../../core/types";
import * as p from "../../core/properties";
export declare class ColorPickerView extends InputWidgetView {
    model: ColorPicker;
    protected input_el: HTMLInputElement;
    connect_signals(): void;
    render(): void;
    change_input(): void;
}
export declare namespace ColorPicker {
    type Attrs = p.AttrsOf<Props>;
    type Props = InputWidget.Props & {
        color: p.Property<Color>;
    };
}
export interface ColorPicker extends ColorPicker.Attrs {
}
export declare class ColorPicker extends InputWidget {
    properties: ColorPicker.Props;
    constructor(attrs?: Partial<ColorPicker.Attrs>);
    static init_ColorPicker(): void;
}
