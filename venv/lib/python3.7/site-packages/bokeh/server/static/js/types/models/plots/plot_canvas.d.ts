import { CartesianFrame } from "../canvas/cartesian_frame";
import { Canvas, CanvasView } from "../canvas/canvas";
import { Range } from "../ranges/range";
import { Renderer, RendererView } from "../renderers/renderer";
import { ToolView } from "../tools/tool";
import { Selection } from "../selections/selection";
import { LayoutDOM, LayoutDOMView } from "../layouts/layout_dom";
import { Plot } from "./plot";
import { Title } from "../annotations/title";
import { AxisView } from "../axes/axis";
import { ToolbarPanel } from "../annotations/toolbar_panel";
import { Arrayable, Interval } from "../../core/types";
import { Signal0 } from "../../core/signaling";
import { UIEvents } from "../../core/ui_events";
import { RenderLevel } from "../../core/enums";
import { Context2d } from "../../core/util/canvas";
import { SizeHint, Size, SizingPolicy, Margin, Layoutable } from "../../core/layout";
import { BBox } from "../../core/util/bbox";
export declare type WebGLState = {
    canvas: HTMLCanvasElement;
    ctx: WebGLRenderingContext;
};
export declare type FrameBox = [number, number, number, number];
export declare type RangeInfo = {
    xrs: {
        [key: string]: Interval;
    };
    yrs: {
        [key: string]: Interval;
    };
};
export declare type StateInfo = {
    range?: RangeInfo;
    selection: {
        [key: string]: Selection;
    };
    dimensions: {
        width: number;
        height: number;
    };
};
export declare class PlotLayout extends Layoutable {
    top_panel: Layoutable;
    bottom_panel: Layoutable;
    left_panel: Layoutable;
    right_panel: Layoutable;
    center_panel: Layoutable;
    min_border: Margin;
    protected _measure(viewport: Size): SizeHint;
    protected _set_geometry(outer: BBox, inner: BBox): void;
}
export declare namespace PlotView {
    type Options = LayoutDOMView.Options & {
        model: Plot;
    };
}
export declare class PlotView extends LayoutDOMView {
    model: Plot;
    visuals: Plot.Visuals;
    layout: PlotLayout;
    frame: CartesianFrame;
    canvas: Canvas;
    canvas_view: CanvasView;
    protected _title: Title;
    protected _toolbar: ToolbarPanel;
    protected _outer_bbox: BBox;
    protected _inner_bbox: BBox;
    protected _needs_paint: boolean;
    protected _needs_layout: boolean;
    gl?: WebGLState;
    force_paint: Signal0<this>;
    state_changed: Signal0<this>;
    visibility_callbacks: ((visible: boolean) => void)[];
    protected _is_paused?: number;
    protected lod_started: boolean;
    protected _initial_state_info: StateInfo;
    protected state: {
        history: {
            type: string;
            info: StateInfo;
        }[];
        index: number;
    };
    protected throttled_paint: () => void;
    protected ui_event_bus: UIEvents;
    computed_renderers: Renderer[];
    renderer_views: {
        [key: string]: RendererView;
    };
    tool_views: {
        [key: string]: ToolView;
    };
    protected range_update_timestamp?: number;
    readonly canvas_overlays: HTMLElement;
    readonly canvas_events: HTMLElement;
    readonly is_paused: boolean;
    readonly child_models: LayoutDOM[];
    pause(): void;
    unpause(no_render?: boolean): void;
    request_render(): void;
    request_paint(): void;
    request_layout(): void;
    reset(): void;
    remove(): void;
    render(): void;
    initialize(): void;
    protected _width_policy(): SizingPolicy;
    protected _height_policy(): SizingPolicy;
    _update_layout(): void;
    readonly axis_views: AxisView[];
    set_cursor(cursor?: string): void;
    set_toolbar_visibility(visible: boolean): void;
    init_webgl(): void;
    prepare_webgl(ratio: number, frame_box: FrameBox): void;
    clear_webgl(): void;
    blit_webgl(): void;
    update_dataranges(): void;
    map_to_screen(x: Arrayable<number>, y: Arrayable<number>, x_name?: string, y_name?: string): [Arrayable<number>, Arrayable<number>];
    push_state(type: string, new_info: Partial<StateInfo>): void;
    clear_state(): void;
    can_undo(): boolean;
    can_redo(): boolean;
    undo(): void;
    redo(): void;
    protected _do_state_change(index: number): void;
    get_selection(): {
        [key: string]: Selection;
    };
    update_selection(selection: {
        [key: string]: Selection;
    } | null): void;
    reset_selection(): void;
    protected _update_ranges_together(range_info_iter: [Range, Interval][]): void;
    protected _update_ranges_individually(range_info_iter: [Range, Interval][], is_panning: boolean, is_scrolling: boolean, maintain_focus: boolean): void;
    protected _get_weight_to_constrain_interval(rng: Range, range_info: Interval): number;
    update_range(range_info: RangeInfo | null, is_panning?: boolean, is_scrolling?: boolean, maintain_focus?: boolean): void;
    reset_range(): void;
    protected _invalidate_layout(): void;
    build_renderer_views(): void;
    get_renderer_views(): RendererView[];
    build_tool_views(): void;
    connect_signals(): void;
    set_initial_range(): void;
    has_finished(): boolean;
    after_layout(): void;
    repaint(): void;
    paint(): void;
    protected _paint_levels(ctx: Context2d, levels: RenderLevel[], clip_region: FrameBox, global_clip: boolean): void;
    protected _map_hook(_ctx: Context2d, _frame_box: FrameBox): void;
    protected _paint_empty(ctx: Context2d, frame_box: FrameBox): void;
    save(name: string): void;
    serializable_state(): {
        [key: string]: unknown;
    };
}
