import { ActionTool, ActionToolView } from "./action_tool";
import { Dimensions } from "../../../core/enums";
import * as p from "../../../core/properties";
export declare class ZoomInToolView extends ActionToolView {
    model: ZoomInTool;
    doit(): void;
}
export declare namespace ZoomInTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = ActionTool.Props & {
        factor: p.Property<number>;
        dimensions: p.Property<Dimensions>;
    };
}
export interface ZoomInTool extends ZoomInTool.Attrs {
}
export declare class ZoomInTool extends ActionTool {
    properties: ZoomInTool.Props;
    constructor(attrs?: Partial<ZoomInTool.Attrs>);
    static init_ZoomInTool(): void;
    tool_name: string;
    icon: string;
    readonly tooltip: string;
}
