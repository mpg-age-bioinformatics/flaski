import { SelectTool, SelectToolView } from "./select_tool";
import { CallbackLike1 } from "../../callbacks/callback";
import { PolyAnnotation } from "../../annotations/poly_annotation";
import { PolyGeometry } from "../../../core/geometry";
import { TapEvent, KeyEvent } from "../../../core/ui_events";
import { Arrayable } from "../../../core/types";
import * as p from "../../../core/properties";
export declare class PolySelectToolView extends SelectToolView {
    model: PolySelectTool;
    protected data: {
        sx: number[];
        sy: number[];
    };
    initialize(): void;
    connect_signals(): void;
    _active_change(): void;
    _keyup(ev: KeyEvent): void;
    _doubletap(ev: TapEvent): void;
    _clear_data(): void;
    _tap(ev: TapEvent): void;
    _do_select(sx: number[], sy: number[], final: boolean, append: boolean): void;
    _emit_callback(geometry: PolyGeometry): void;
}
export declare namespace PolySelectTool {
    type Attrs = p.AttrsOf<Props>;
    type Props = SelectTool.Props & {
        callback: p.Property<CallbackLike1<PolySelectTool, {
            geometry: PolyGeometry & {
                x: Arrayable<number>;
                y: Arrayable<number>;
            };
        }> | null>;
        overlay: p.Property<PolyAnnotation>;
    };
}
export interface PolySelectTool extends PolySelectTool.Attrs {
}
export declare class PolySelectTool extends SelectTool {
    properties: PolySelectTool.Props;
    overlay: PolyAnnotation;
    constructor(attrs?: Partial<PolySelectTool.Attrs>);
    static init_PolySelectTool(): void;
    tool_name: string;
    icon: string;
    event_type: "tap";
    default_order: number;
}
