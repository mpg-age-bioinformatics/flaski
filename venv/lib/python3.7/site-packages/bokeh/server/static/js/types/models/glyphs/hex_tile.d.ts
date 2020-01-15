import { Glyph, GlyphView, GlyphData } from "./glyph";
import { PointGeometry, RectGeometry, SpanGeometry } from "../../core/geometry";
import * as p from "../../core/properties";
import { LineVector, FillVector } from "../../core/property_mixins";
import { Arrayable, Rect } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import { SpatialIndex } from "../../core/util/spatial";
import { Line, Fill } from "../../core/visuals";
import { HexTileOrientation } from "../../core/enums";
import { Selection } from "../selections/selection";
export interface HexTileData extends GlyphData {
    _q: Arrayable<number>;
    _r: Arrayable<number>;
    _x: Arrayable<number>;
    _y: Arrayable<number>;
    _scale: Arrayable<number>;
    sx: Arrayable<number>;
    sy: Arrayable<number>;
    svx: number[];
    svy: number[];
    ssize: number;
}
export interface HexTileView extends HexTileData {
}
export declare class HexTileView extends GlyphView {
    model: HexTile;
    visuals: HexTile.Visuals;
    scenterx(i: number): number;
    scentery(i: number): number;
    protected _set_data(): void;
    protected _index_data(): SpatialIndex;
    map_data(): void;
    protected _get_unscaled_vertices(): [number[], number[]];
    protected _render(ctx: Context2d, indices: number[], { sx, sy, svx, svy, _scale }: HexTileData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    protected _hit_span(geometry: SpanGeometry): Selection;
    protected _hit_rect(geometry: RectGeometry): Selection;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace HexTile {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & LineVector & FillVector & {
        r: p.NumberSpec;
        q: p.NumberSpec;
        size: p.Property<number>;
        aspect_scale: p.Property<number>;
        scale: p.NumberSpec;
        orientation: p.Property<HexTileOrientation>;
    };
    type Visuals = Glyph.Visuals & {
        line: Line;
        fill: Fill;
    };
}
export interface HexTile extends HexTile.Attrs {
}
export declare class HexTile extends Glyph {
    properties: HexTile.Props;
    constructor(attrs?: Partial<HexTile.Attrs>);
    static init_HexTile(): void;
}
