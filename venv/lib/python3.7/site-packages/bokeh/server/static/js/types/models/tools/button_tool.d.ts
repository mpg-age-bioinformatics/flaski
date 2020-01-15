import { Class } from "../../core/class";
import { DOMView } from "../../core/dom_view";
import { Tool, ToolView } from "./tool";
import * as p from "../../core/properties";
export declare abstract class ButtonToolButtonView extends DOMView {
    model: ButtonTool;
    initialize(): void;
    css_classes(): string[];
    render(): void;
    protected abstract _clicked(): void;
}
export declare abstract class ButtonToolView extends ToolView {
    model: ButtonTool;
}
export declare namespace ButtonTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = Tool.Props & {
        disabled: p.Property<boolean>;
    };
}
export interface ButtonTool extends ButtonTool.Attrs {
}
export declare abstract class ButtonTool extends Tool {
    properties: ButtonTool.Props;
    constructor(attrs?: Partial<ButtonTool.Attrs>);
    static init_ButtonTool(): void;
    tool_name: string;
    icon: string;
    button_view: Class<ButtonToolButtonView>;
    readonly tooltip: string;
    readonly computed_icon: string;
}
