import * as p from "../../core/properties";
import { Widget, WidgetView } from "./widget";
export declare class FileInputView extends WidgetView {
    model: FileInput;
    protected dialogEl: HTMLInputElement;
    connect_signals(): void;
    render(): void;
    load_file(e: any): void;
    file(e: any): void;
}
export declare namespace FileInput {
    type Attrs = p.AttrsOf<Props>;
    type Props = Widget.Props & {
        value: p.Property<string>;
        mime_type: p.Property<string>;
        filename: p.Property<string>;
        accept: p.Property<string>;
    };
}
export interface FileInput extends FileInput.Attrs {
}
export declare abstract class FileInput extends Widget {
    properties: FileInput.Props;
    constructor(attrs?: Partial<FileInput.Attrs>);
    static init_FileInput(): void;
}
