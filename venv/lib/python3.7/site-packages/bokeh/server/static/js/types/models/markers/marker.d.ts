import { RenderOne } from "./defs";
import { XYGlyph, XYGlyphView, XYGlyphData } from "../glyphs/xy_glyph";
import { PointGeometry, SpanGeometry, RectGeometry, PolyGeometry } from "../../core/geometry";
import { LineVector, FillVector } from "../../core/property_mixins";
import { Line, Fill } from "../../core/visuals";
import { Arrayable, Rect } from "../../core/types";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export interface MarkerData extends XYGlyphData {
    _size: Arrayable<number>;
    _angle: Arrayable<number>;
    max_size: number;
}
export interface MarkerView extends MarkerData {
}
export declare abstract class MarkerView extends XYGlyphView {
    model: Marker;
    visuals: Marker.Visuals;
    protected _render_one: RenderOne;
    protected _render(ctx: Context2d, indices: number[], { sx, sy, _size, _angle }: MarkerData): void;
    protected _mask_data(): number[];
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    protected _hit_rect(geometry: RectGeometry): Selection;
    protected _hit_poly(geometry: PolyGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, { x0, x1, y0, y1 }: Rect, index: number): void;
}
export declare namespace Marker {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & FillVector & {
        size: p.DistanceSpec;
        angle: p.AngleSpec;
    };
    type Visuals = XYGlyph.Visuals & {
        line: Line;
        fill: Fill;
    };
}
export interface Marker extends Marker.Attrs {
}
export declare abstract class Marker extends XYGlyph {
    properties: Marker.Props;
    constructor(attrs?: Partial<Marker.Attrs>);
    static init_Marker(): void;
}
