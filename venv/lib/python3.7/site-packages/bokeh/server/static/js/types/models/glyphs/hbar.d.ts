import { Box, BoxView, BoxData } from "./box";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
import { SpatialIndex } from "../../core/util/spatial";
export interface HBarData extends BoxData {
    _left: Arrayable<number>;
    _y: Arrayable<number>;
    _height: Arrayable<number>;
    _right: Arrayable<number>;
    sy: Arrayable<number>;
    sh: Arrayable<number>;
    sleft: Arrayable<number>;
    sright: Arrayable<number>;
    stop: Arrayable<number>;
    sbottom: Arrayable<number>;
    max_height: number;
}
export interface HBarView extends HBarData {
}
export declare class HBarView extends BoxView {
    model: HBar;
    visuals: HBar.Visuals;
    scenterx(i: number): number;
    scentery(i: number): number;
    protected _index_data(): SpatialIndex;
    protected _lrtb(i: number): [number, number, number, number];
    protected _map_data(): void;
}
export declare namespace HBar {
    type Attrs = p.AttrsOf<Props>;
    type Props = Box.Props & {
        left: p.CoordinateSpec;
        y: p.CoordinateSpec;
        height: p.NumberSpec;
        right: p.CoordinateSpec;
    };
    type Visuals = Box.Visuals;
}
export interface HBar extends HBar.Attrs {
}
export declare class HBar extends Box {
    properties: HBar.Props;
    constructor(attrs?: Partial<HBar.Attrs>);
    static init_HBar(): void;
}
