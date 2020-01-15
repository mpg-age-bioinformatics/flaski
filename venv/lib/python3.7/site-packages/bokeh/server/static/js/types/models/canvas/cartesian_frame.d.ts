import { Scale } from "../scales/scale";
import { Range } from "../ranges/range";
import { Range1d } from "../ranges/range1d";
import { LayoutItem } from "../../core/layout";
import { Arrayable } from "../../core/types";
import { BBox } from "../../core/util/bbox";
export declare type Ranges = {
    [key: string]: Range;
};
export declare type Scales = {
    [key: string]: Scale;
};
export declare class CartesianFrame extends LayoutItem {
    readonly x_scale: Scale;
    readonly y_scale: Scale;
    readonly x_range: Range;
    readonly y_range: Range;
    readonly extra_x_ranges: Ranges;
    readonly extra_y_ranges: Ranges;
    constructor(x_scale: Scale, y_scale: Scale, x_range: Range, y_range: Range, extra_x_ranges?: Ranges, extra_y_ranges?: Ranges);
    protected _h_target: Range1d;
    protected _v_target: Range1d;
    protected _x_ranges: Ranges;
    protected _y_ranges: Ranges;
    protected _xscales: Scales;
    protected _yscales: Scales;
    map_to_screen(x: Arrayable<number>, y: Arrayable<number>, x_name?: string, y_name?: string): [Arrayable<number>, Arrayable<number>];
    protected _get_ranges(range: Range, extra_ranges?: Ranges): Ranges;
    _get_scales(scale: Scale, ranges: Ranges, frame_range: Range): Scales;
    protected _configure_frame_ranges(): void;
    protected _configure_scales(): void;
    protected _update_scales(): void;
    protected _set_geometry(outer: BBox, inner: BBox): void;
    readonly x_ranges: Ranges;
    readonly y_ranges: Ranges;
    readonly xscales: Scales;
    readonly yscales: Scales;
}
