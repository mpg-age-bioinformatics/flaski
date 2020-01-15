import { ActionTool, ActionToolView } from "./action_tool";
import * as p from "../../../core/properties";
export declare class SaveToolView extends ActionToolView {
    model: SaveTool;
    doit(): void;
}
export declare namespace SaveTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = ActionTool.Props;
}
export interface SaveTool extends SaveTool.Attrs {
}
export declare class SaveTool extends ActionTool {
    properties: SaveTool.Props;
    constructor(attrs?: Partial<SaveTool.Attrs>);
    static init_SaveTool(): void;
    tool_name: string;
    icon: string;
}
