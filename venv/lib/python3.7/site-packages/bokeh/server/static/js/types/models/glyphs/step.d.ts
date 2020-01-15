import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector } from "../../core/property_mixins";
import { Line } from "../../core/visuals";
import * as p from "../../core/properties";
import { Rect } from "../../core/types";
import { StepMode } from "../../core/enums";
import { Context2d } from "../../core/util/canvas";
export interface StepData extends XYGlyphData {
}
export interface StepView extends StepData {
}
export declare class StepView extends XYGlyphView {
    model: Step;
    visuals: Step.Visuals;
    protected _render(ctx: Context2d, indices: number[], { sx, sy }: StepData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Rect, index: number): void;
}
export declare namespace Step {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & {
        mode: p.Property<StepMode>;
    };
    type Visuals = XYGlyph.Visuals & {
        line: Line;
    };
}
export interface Step extends Step.Attrs {
}
export declare class Step extends XYGlyph {
    properties: Step.Props;
    constructor(attrs?: Partial<Step.Attrs>);
    static init_Step(): void;
}
