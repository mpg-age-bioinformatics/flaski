import { GestureTool, GestureToolView } from "./gesture_tool";
import { DataRenderer } from "../../renderers/data_renderer";
import { RendererSpec } from "../util";
import * as p from "../../../core/properties";
import { KeyEvent } from "../../../core/ui_events";
import { Geometry } from "../../../core/geometry";
export declare abstract class SelectToolView extends GestureToolView {
    model: SelectTool;
    readonly computed_renderers: DataRenderer[];
    _computed_renderers_by_data_source(): {
        [key: string]: DataRenderer[];
    };
    _keyup(ev: KeyEvent): void;
    _select(geometry: Geometry, final: boolean, append: boolean): void;
    _emit_selection_event(geometry: Geometry, final?: boolean): void;
}
export declare namespace SelectTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = GestureTool.Props & {
        renderers: p.Property<RendererSpec>;
        names: p.Property<string[]>;
    };
}
export interface SelectTool extends SelectTool.Attrs {
}
export declare abstract class SelectTool extends GestureTool {
    properties: SelectTool.Props;
    constructor(attrs?: Partial<SelectTool.Attrs>);
    static init_SelectTool(): void;
}
