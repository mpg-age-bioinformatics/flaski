import { SpatialIndex } from "../../core/util/spatial";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { Arrayable, Rect } from "../../core/types";
import { PointGeometry } from "../../core/geometry";
import { Context2d } from "../../core/util/canvas";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Line, Fill, Hatch } from "../../core/visuals";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export interface MultiPolygonsData extends GlyphData {
    _xs: Arrayable<Arrayable<Arrayable<Arrayable<number>>>>;
    _ys: Arrayable<Arrayable<Arrayable<Arrayable<number>>>>;
    sxs: Arrayable<Arrayable<Arrayable<Arrayable<number>>>>;
    sys: Arrayable<Arrayable<Arrayable<Arrayable<number>>>>;
    hole_index: SpatialIndex;
}
export interface MultiPolygonsView extends MultiPolygonsData {
}
export declare class MultiPolygonsView extends GlyphView {
    model: MultiPolygons;
    visuals: MultiPolygons.Visuals;
    protected _index_data(): SpatialIndex;
    protected _index_hole_data(): SpatialIndex;
    protected _mask_data(): number[];
    protected _inner_loop(ctx: Context2d, sx: Arrayable<Arrayable<Arrayable<number>>>, sy: Arrayable<Arrayable<Arrayable<number>>>): void;
    protected _render(ctx: Context2d, indices: number[], { sxs, sys }: MultiPolygonsData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    private _get_snap_coord;
    scenterx(i: number, sx: number, sy: number): number;
    scentery(i: number, sx: number, sy: number): number;
    map_data(): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace MultiPolygons {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & LineVector & FillVector & HatchVector & {
        xs: p.CoordinateSeqSpec;
        ys: p.CoordinateSeqSpec;
    };
    type Visuals = Glyph.Visuals & {
        line: Line;
        fill: Fill;
        hatch: Hatch;
    };
}
export interface MultiPolygons extends MultiPolygons.Attrs {
}
export declare class MultiPolygons extends Glyph {
    properties: MultiPolygons.Props;
    constructor(attrs?: Partial<MultiPolygons.Attrs>);
    static init_MultiPolygons(): void;
}
