import { Size, Sizeable, SizeHint, BoxSizing } from "./types";
import { BBox, CoordinateTransform } from "../util/bbox";
export interface ComputedVariable {
    readonly value: number;
}
export declare type ExtBoxSizing = BoxSizing & {
    readonly size: Partial<Size>;
    readonly min_size: Size;
    readonly max_size: Size;
};
export declare abstract class Layoutable {
    protected _bbox: BBox;
    protected _inner_bbox: BBox;
    readonly bbox: BBox;
    readonly inner_bbox: BBox;
    _top: ComputedVariable;
    _left: ComputedVariable;
    _width: ComputedVariable;
    _height: ComputedVariable;
    _right: ComputedVariable;
    _bottom: ComputedVariable;
    _hcenter: ComputedVariable;
    _vcenter: ComputedVariable;
    private _sizing;
    readonly sizing: ExtBoxSizing;
    set_sizing(sizing: Partial<BoxSizing>): void;
    protected _init(): void;
    constructor();
    protected _set_geometry(outer: BBox, inner: BBox): void;
    set_geometry(outer: BBox, inner?: BBox): void;
    is_width_expanding(): boolean;
    is_height_expanding(): boolean;
    apply_aspect(viewport: Size, { width, height }: Size): Size;
    protected abstract _measure(viewport: Sizeable): SizeHint;
    measure(viewport_size: Size): SizeHint;
    compute(viewport?: Partial<Size>): void;
    readonly xview: CoordinateTransform;
    readonly yview: CoordinateTransform;
    clip_width(width: number): number;
    clip_height(height: number): number;
    clip_size({ width, height }: Size): Size;
}
export declare class LayoutItem extends Layoutable {
    protected _measure(viewport: Size): SizeHint;
}
export declare abstract class ContentLayoutable extends Layoutable {
    protected abstract _content_size(): Sizeable;
    protected _measure(viewport: Sizeable): SizeHint;
}
