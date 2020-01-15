import { Arrayable } from "../../core/types";
import { SpatialIndex } from "../../core/util/spatial";
import * as p from "../../core/properties";
import { Glyph, GlyphView, GlyphData } from "./glyph";
export interface XYGlyphData extends GlyphData {
    _x: Arrayable<number>;
    _y: Arrayable<number>;
    sx: Arrayable<number>;
    sy: Arrayable<number>;
}
export interface XYGlyphView extends XYGlyphData {
}
export declare abstract class XYGlyphView extends GlyphView {
    model: XYGlyph;
    visuals: XYGlyph.Visuals;
    protected _index_data(): SpatialIndex;
    scenterx(i: number): number;
    scentery(i: number): number;
}
export declare namespace XYGlyph {
    type Attrs = p.AttrsOf<Props>;
    type Props = Glyph.Props & {
        x: p.CoordinateSpec;
        y: p.CoordinateSpec;
    };
    type Visuals = Glyph.Visuals;
}
export interface XYGlyph extends XYGlyph.Attrs {
}
export declare abstract class XYGlyph extends Glyph {
    properties: XYGlyph.Props;
    constructor(attrs?: Partial<XYGlyph.Attrs>);
    static init_XYGlyph(): void;
}
