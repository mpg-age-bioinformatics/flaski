import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { PointGeometry } from "../../core/geometry";
import { LineVector, FillVector } from "../../core/property_mixins";
import { Line, Fill } from "../../core/visuals";
import { Arrayable, Rect } from "../../core/types";
import { Direction } from "../../core/enums";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export interface WedgeData extends XYGlyphData {
    _radius: Arrayable<number>;
    _start_angle: Arrayable<number>;
    _end_angle: Arrayable<number>;
    sradius: Arrayable<number>;
    max_radius: number;
}
export interface WedgeView extends WedgeData {
}
export declare class WedgeView extends XYGlyphView {
    model: Wedge;
    visuals: Wedge.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], { sx, sy, sradius, _start_angle, _end_angle }: WedgeData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
    private _scenterxy;
    scenterx(i: number): number;
    scentery(i: number): number;
}
export declare namespace Wedge {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & FillVector & {
        direction: p.Property<Direction>;
        radius: p.DistanceSpec;
        start_angle: p.AngleSpec;
        end_angle: p.AngleSpec;
    };
    type Visuals = XYGlyph.Visuals & {
        line: Line;
        fill: Fill;
    };
}
export interface Wedge extends Wedge.Attrs {
}
export declare class Wedge extends XYGlyph {
    properties: Wedge.Props;
    constructor(attrs?: Partial<Wedge.Attrs>);
    static init_Wedge(): void;
}
