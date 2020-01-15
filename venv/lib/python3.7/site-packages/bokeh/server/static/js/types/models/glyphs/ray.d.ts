import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector } from "../../core/property_mixins";
import { Line } from "../../core/visuals";
import { Arrayable, Rect } from "../../core/types";
import { Class } from "../../core/class";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
export interface RayData extends XYGlyphData {
    _length: Arrayable<number>;
    _angle: Arrayable<number>;
    slength: Arrayable<number>;
}
export interface RayView extends RayData {
}
export declare class RayView extends XYGlyphView {
    model: Ray;
    visuals: Ray.Visuals;
    protected _map_data(): void;
    protected _render(ctx: Context2d, indices: number[], { sx, sy, slength, _angle }: RayData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Ray {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & {
        length: p.DistanceSpec;
        angle: p.AngleSpec;
    };
    type Visuals = XYGlyph.Visuals & {
        line: Line;
    };
}
export interface Ray extends Ray.Attrs {
}
export declare class Ray extends XYGlyph {
    properties: Ray.Props;
    default_view: Class<RayView>;
    constructor(attrs?: Partial<Ray.Attrs>);
    static init_Ray(): void;
}
