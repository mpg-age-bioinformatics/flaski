import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { TextVector } from "../../core/property_mixins";
import { PointGeometry } from "../../core/geometry";
import { Arrayable } from "../../core/types";
import * as visuals from "../../core/visuals";
import * as p from "../../core/properties";
import { Context2d } from "../../core/util/canvas";
import { Selection } from "../selections/selection";
export interface TextData extends XYGlyphData {
    _text: Arrayable<string>;
    _angle: Arrayable<number>;
    _x_offset: Arrayable<number>;
    _y_offset: Arrayable<number>;
    _sxs: number[][][];
    _sys: number[][][];
}
export interface TextView extends TextData {
}
export declare class TextView extends XYGlyphView {
    model: Text;
    visuals: Text.Visuals;
    private _rotate_point;
    private _text_bounds;
    protected _render(ctx: Context2d, indices: number[], { sx, sy, _x_offset, _y_offset, _angle, _text }: TextData): void;
    protected _hit_point(geometry: PointGeometry): Selection;
    private _scenterxy;
    scenterx(i: number): number;
    scentery(i: number): number;
}
export declare namespace Text {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & TextVector & {
        text: p.NullStringSpec;
        angle: p.AngleSpec;
        x_offset: p.NumberSpec;
        y_offset: p.NumberSpec;
    };
    type Visuals = XYGlyph.Visuals & {
        text: visuals.Text;
    };
}
export interface Text extends Text.Attrs {
}
export declare class Text extends XYGlyph {
    properties: Text.Props;
    constructor(attrs?: Partial<Text.Attrs>);
    static init_Text(): void;
}
