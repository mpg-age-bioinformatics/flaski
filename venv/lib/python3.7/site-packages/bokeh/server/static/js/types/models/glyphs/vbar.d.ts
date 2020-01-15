import { Box, BoxView, BoxData } from "./box";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
import { SpatialIndex } from "../../core/util/spatial";
export interface VBarData extends BoxData {
    _x: Arrayable<number>;
    _bottom: Arrayable<number>;
    _width: Arrayable<number>;
    _top: Arrayable<number>;
    sx: Arrayable<number>;
    sw: Arrayable<number>;
    stop: Arrayable<number>;
    sbottom: Arrayable<number>;
    sleft: Arrayable<number>;
    sright: Arrayable<number>;
    max_width: number;
}
export interface VBarView extends VBarData {
}
export declare class VBarView extends BoxView {
    model: VBar;
    visuals: VBar.Visuals;
    scenterx(i: number): number;
    scentery(i: number): number;
    protected _index_data(): SpatialIndex;
    protected _lrtb(i: number): [number, number, number, number];
    protected _map_data(): void;
}
export declare namespace VBar {
    type Attrs = p.AttrsOf<Props>;
    type Props = Box.Props & {
        x: p.CoordinateSpec;
        bottom: p.CoordinateSpec;
        width: p.NumberSpec;
        top: p.CoordinateSpec;
    };
    type Visuals = Box.Visuals;
}
export interface VBar extends VBar.Attrs {
}
export declare class VBar extends Box {
    properties: VBar.Props;
    constructor(attrs?: Partial<VBar.Attrs>);
    static init_VBar(): void;
}
