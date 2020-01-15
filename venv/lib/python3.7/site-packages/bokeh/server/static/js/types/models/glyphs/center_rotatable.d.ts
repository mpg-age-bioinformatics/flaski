import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector, FillVector } from "../../core/property_mixins";
import { Line, Fill } from "../../core/visuals";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export interface CenterRotatableData extends XYGlyphData {
    _angle: Arrayable<number>;
    _width: Arrayable<number>;
    _height: Arrayable<number>;
    sw: Arrayable<number>;
    sh: Arrayable<number>;
    max_width: number;
    max_height: number;
    max_w2: number;
    max_h2: number;
}
export interface CenterRotatableView extends CenterRotatableData {
}
export declare abstract class CenterRotatableView extends XYGlyphView {
    model: CenterRotatable;
    visuals: CenterRotatable.Visuals;
}
export declare namespace CenterRotatable {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & FillVector & {
        angle: p.AngleSpec;
        width: p.DistanceSpec;
        height: p.DistanceSpec;
    };
    type Visuals = XYGlyph.Visuals & {
        line: Line;
        fill: Fill;
    };
}
export interface CenterRotatable extends CenterRotatable.Attrs {
}
export declare abstract class CenterRotatable extends XYGlyph {
    properties: CenterRotatable.Props;
    constructor(attrs?: Partial<CenterRotatable.Attrs>);
    static init_CenterRotatable(): void;
}
