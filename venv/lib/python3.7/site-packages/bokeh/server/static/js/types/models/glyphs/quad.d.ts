import { Box, BoxView, BoxData } from "./box";
import { Arrayable } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
export interface QuadData extends BoxData {
    _right: Arrayable<number>;
    _bottom: Arrayable<number>;
    _left: Arrayable<number>;
    _top: Arrayable<number>;
    sright: Arrayable<number>;
    sbottom: Arrayable<number>;
    sleft: Arrayable<number>;
    stop: Arrayable<number>;
}
export interface QuadView extends QuadData {
}
export declare class QuadView extends BoxView {
    model: Quad;
    visuals: Quad.Visuals;
    scenterx(i: number): number;
    scentery(i: number): number;
    protected _index_data(): SpatialIndex;
    protected _lrtb(i: number): [number, number, number, number];
}
export declare namespace Quad {
    type Attrs = p.AttrsOf<Props>;
    type Props = Box.Props & {
        right: p.CoordinateSpec;
        bottom: p.CoordinateSpec;
        left: p.CoordinateSpec;
        top: p.CoordinateSpec;
    };
    type Visuals = Box.Visuals;
}
export interface Quad extends Quad.Attrs {
}
export declare class Quad extends Box {
    properties: Quad.Props;
    constructor(attrs?: Partial<Quad.Attrs>);
    static init_Quad(): void;
}
