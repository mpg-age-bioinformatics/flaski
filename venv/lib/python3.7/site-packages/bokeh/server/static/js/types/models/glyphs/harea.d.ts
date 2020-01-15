import { PointGeometry } from "../../core/geometry";
import { Arrayable } from "../../core/types";
import { Area, AreaView, AreaData } from "./area";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export interface HAreaData extends AreaData {
    _x1: Arrayable<number>;
    _x2: Arrayable<number>;
    _y: Arrayable<number>;
    sx1: Arrayable<number>;
    sx2: Arrayable<number>;
    sy: Arrayable<number>;
}
export interface HAreaView extends HAreaData {
}
export declare class HAreaView extends AreaView {
    model: HArea;
    visuals: HArea.Visuals;
    protected _index_data(): SpatialIndex;
    protected _inner(ctx: Context2d, sx1: Arrayable<number>, sx2: Arrayable<number>, sy: Arrayable<number>, func: (this: Context2d) => void): void;
    protected _render(ctx: Context2d, _indices: number[], { sx1, sx2, sy }: HAreaData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    scenterx(i: number): number;
    scentery(i: number): number;
    protected _map_data(): void;
}
export declare namespace HArea {
    type Attrs = p.AttrsOf<Props>;
    type Props = Area.Props & {
        x1: p.CoordinateSpec;
        x2: p.CoordinateSpec;
        y: p.CoordinateSpec;
    };
    type Visuals = Area.Visuals;
}
export interface HArea extends HArea.Attrs {
}
export declare class HArea extends Area {
    properties: HArea.Props;
    constructor(attrs?: Partial<HArea.Attrs>);
    static init_HArea(): void;
}
