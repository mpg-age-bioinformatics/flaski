import { TextInput } from "./text_input";
import { InputWidgetView } from "./input_widget";
import * as p from "../../core/properties";
export declare class TextAreaInputView extends InputWidgetView {
    model: TextAreaInput;
    protected input_el: HTMLTextAreaElement;
    connect_signals(): void;
    render(): void;
    change_input(): void;
}
export declare namespace TextAreaInput {
    type Attrs = p.AttrsOf<Props>;
    type Props = TextInput.Props & {
        cols: p.Property<number>;
        rows: p.Property<number>;
        max_length: p.Property<number>;
    };
}
export interface TextAreaInput extends TextAreaInput.Attrs {
}
export declare class TextAreaInput extends TextInput {
    properties: TextAreaInput.Props;
    constructor(attrs?: Partial<TextAreaInput.Attrs>);
    static init_TextAreaInput(): void;
}
