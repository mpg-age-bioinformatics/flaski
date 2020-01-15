import { SpatialIndex } from "../../core/util/spatial";
import { Glyph, GlyphView, GlyphData } from "./glyph";
import { Arrayable, Rect } from "../../core/types";
import { PointGeometry } from "../../core/geometry";
import { Context2d } from "../../core/util/canvas";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Line, Fill, Hatch } from "../../core/visuals";
import * as p from "../../core/properties";
import { Selection } from "../selections/selection";
export interface PatchesData extends GlyphData {
    _xs: Arrayable<Arrayable<number>>;
    _ys: Arrayable<Arrayable<number>>;
    sxs: Arrayable<Arrayable<number>>;
    sys: Arrayable<Arrayable<number>>;
    sxss: number[][][];
    syss: number[][][];
}
export interface PatchesView extends PatchesData {
}
export declare class PatchesView extends GlyphView {
    model: Patches;
    visuals: Patches.Visuals;
    private _build_discontinuous_object;
    protected _index_data(): SpatialIndex;
    protected _mask_data(): number[];
    protected _inner_loop(ctx: Context2d, sx: Arrayable<number>, sy: Arrayable<number>, func: (this: Context2d) => void): void;
    protected _render(ctx: Context2d, indices: number[], { sxs, sys }: PatchesData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    private _get_snap_coord;
    scenterx(i: number, sx: number, sy: number): number;
    scentery(i: number, sx: number, sy: number): number;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Patches {
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
export interface Patches extends Patches.Attrs {
}
export declare class Patches extends Glyph {
    properties: Patches.Props;
    constructor(attrs?: Partial<Patches.Attrs>);
    static init_Patches(): void;
}
