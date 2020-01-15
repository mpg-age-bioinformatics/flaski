import * as p from "../../core/properties";
import { View } from "../../core/view";
import { Dimensions } from "../../core/enums";
import { Model } from "../../model";
import { Renderer } from "../renderers/renderer";
import { CartesianFrame } from "../canvas/cartesian_frame";
import { Plot, PlotView } from "../plots/plot";
import { Annotation } from "../annotations/annotation";
import { EventType, PanEvent, PinchEvent, RotateEvent, ScrollEvent, TapEvent, MoveEvent, KeyEvent } from "../../core/ui_events";
export declare abstract class ToolView extends View {
    model: Tool;
    parent: PlotView;
    readonly plot_view: PlotView;
    readonly plot_model: Plot;
    connect_signals(): void;
    activate(): void;
    deactivate(): void;
    _pan_start?(e: PanEvent): void;
    _pan?(e: PanEvent): void;
    _pan_end?(e: PanEvent): void;
    _pinch_start?(e: PinchEvent): void;
    _pinch?(e: PinchEvent): void;
    _pinch_end?(e: PinchEvent): void;
    _rotate_start?(e: RotateEvent): void;
    _rotate?(e: RotateEvent): void;
    _rotate_end?(e: RotateEvent): void;
    _tap?(e: TapEvent): void;
    _doubletap?(e: TapEvent): void;
    _press?(e: TapEvent): void;
    _pressup?(e: TapEvent): void;
    _move_enter?(e: MoveEvent): void;
    _move?(e: MoveEvent): void;
    _move_exit?(e: MoveEvent): void;
    _scroll?(e: ScrollEvent): void;
    _keydown?(e: KeyEvent): void;
    _keyup?(e: KeyEvent): void;
}
export declare namespace Tool {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        active: p.Property<boolean>;
    };
}
export interface Tool extends Tool.Attrs {
    overlay?: Annotation;
}
export declare abstract class Tool extends Model {
    properties: Tool.Props;
    constructor(attrs?: Partial<Tool.Attrs>);
    static init_Tool(): void;
    readonly event_type?: EventType | EventType[];
    readonly synthetic_renderers: Renderer[];
    protected _get_dim_tooltip(name: string, dims: Dimensions): string;
    _get_dim_limits([sx0, sy0]: [number, number], [sx1, sy1]: [number, number], frame: CartesianFrame, dims: Dimensions): [[number, number], [number, number]];
}
