import { Annotation, AnnotationView } from "./annotation";
import { Toolbar } from "../tools/toolbar";
import { ToolbarBaseView } from "../tools/toolbar_base";
import { Size } from "../../core/layout";
import * as p from "../../core/properties";
export declare class ToolbarPanelView extends AnnotationView {
    model: ToolbarPanel;
    readonly rotate: boolean;
    protected _toolbar_views: {
        [key: string]: ToolbarBaseView;
    };
    initialize(): void;
    remove(): void;
    render(): void;
    protected _get_size(): Size;
}
export declare namespace ToolbarPanel {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & {
        toolbar: p.Property<Toolbar>;
    };
}
export interface ToolbarPanel extends ToolbarPanel.Attrs {
}
export declare class ToolbarPanel extends Annotation {
    properties: ToolbarPanel.Props;
    constructor(attrs?: Partial<ToolbarPanel.Attrs>);
    static init_ToolbarPanel(): void;
}
