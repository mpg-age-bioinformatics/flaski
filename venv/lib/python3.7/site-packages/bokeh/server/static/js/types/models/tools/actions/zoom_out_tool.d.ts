import { ActionTool, ActionToolView } from "./action_tool";
import { Dimensions } from "../../../core/enums";
import * as p from "../../../core/properties";
export declare class ZoomOutToolView extends ActionToolView {
    model: ZoomOutTool;
    doit(): void;
}
export declare namespace ZoomOutTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = ActionTool.Props & {
        factor: p.Property<number>;
        dimensions: p.Property<Dimensions>;
    };
}
export interface ZoomOutTool extends ZoomOutTool.Attrs {
}
export declare class ZoomOutTool extends ActionTool {
    properties: ZoomOutTool.Props;
    constructor(attrs?: Partial<ZoomOutTool.Attrs>);
    static init_ZoomOutTool(): void;
    tool_name: string;
    icon: string;
    readonly tooltip: string;
}
