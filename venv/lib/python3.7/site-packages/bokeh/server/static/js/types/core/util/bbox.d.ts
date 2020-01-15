import { Arrayable, Rect, Box, Interval } from "../types";
export declare function empty(): Rect;
export declare function positive_x(): Rect;
export declare function positive_y(): Rect;
export declare function union(a: Rect, b: Rect): Rect;
export declare type HorizontalPosition = {
    left: number;
    width: number;
} | {
    width: number;
    right: number;
} | {
    left: number;
    right: number;
} | {
    hcenter: number;
    width: number;
};
export declare type VerticalPosition = {
    top: number;
    height: number;
} | {
    height: number;
    bottom: number;
} | {
    top: number;
    bottom: number;
} | {
    vcenter: number;
    height: number;
};
export declare type Position = HorizontalPosition & VerticalPosition;
export interface CoordinateTransform {
    compute: (v: number) => number;
    v_compute: (vv: Arrayable<number>) => Arrayable<number>;
}
export declare class BBox implements Rect {
    readonly x0: number;
    readonly y0: number;
    readonly x1: number;
    readonly y1: number;
    constructor(box?: Rect | Box | Position);
    toString(): string;
    readonly left: number;
    readonly top: number;
    readonly right: number;
    readonly bottom: number;
    readonly p0: [number, number];
    readonly p1: [number, number];
    readonly x: number;
    readonly y: number;
    readonly width: number;
    readonly height: number;
    readonly rect: Rect;
    readonly box: Box;
    readonly h_range: Interval;
    readonly v_range: Interval;
    readonly ranges: [Interval, Interval];
    readonly aspect: number;
    readonly hcenter: number;
    readonly vcenter: number;
    contains(x: number, y: number): boolean;
    clip(x: number, y: number): [number, number];
    union(that: Rect): BBox;
    equals(that: Rect): boolean;
    readonly xview: CoordinateTransform;
    readonly yview: CoordinateTransform;
}
