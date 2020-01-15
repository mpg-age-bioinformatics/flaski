import { TextAnnotation, TextAnnotationView } from "./text_annotation";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { TextVector } from "../../core/property_mixins";
import { LineJoin, LineCap } from "../../core/enums";
import { SpatialUnits } from "../../core/enums";
import * as p from "../../core/properties";
import { Size } from "../../core/layout";
import { Arrayable } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
export declare class LabelSetView extends TextAnnotationView {
    model: LabelSet;
    visuals: LabelSet.Visuals;
    protected _x: Arrayable<number>;
    protected _y: Arrayable<number>;
    protected _text: Arrayable<string>;
    protected _angle: Arrayable<number>;
    protected _x_offset: Arrayable<number>;
    protected _y_offset: Arrayable<number>;
    initialize(): void;
    connect_signals(): void;
    set_data(source: ColumnarDataSource): void;
    protected _map_data(): [Arrayable<number>, Arrayable<number>];
    render(): void;
    protected _get_size(): Size;
    protected _v_canvas_text(ctx: Context2d, i: number, text: string, sx: number, sy: number, angle: number): void;
    protected _v_css_text(ctx: Context2d, i: number, text: string, sx: number, sy: number, angle: number): void;
}
export declare namespace LabelSet {
    type Attrs = p.AttrsOf<Props>;
    type Props = TextAnnotation.Props & TextVector & {
        x: p.NumberSpec;
        y: p.NumberSpec;
        x_units: p.Property<SpatialUnits>;
        y_units: p.Property<SpatialUnits>;
        text: p.StringSpec;
        angle: p.AngleSpec;
        x_offset: p.NumberSpec;
        y_offset: p.NumberSpec;
        source: p.Property<ColumnarDataSource>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
        border_line_color: p.ColorSpec;
        border_line_width: p.NumberSpec;
        border_line_alpha: p.NumberSpec;
        border_line_join: p.Property<LineJoin>;
        border_line_cap: p.Property<LineCap>;
        border_line_dash: p.Property<number[]>;
        border_line_dash_offset: p.Property<number>;
        background_fill_color: p.ColorSpec;
        background_fill_alpha: p.NumberSpec;
    };
    type Visuals = TextAnnotation.Visuals;
}
export interface LabelSet extends LabelSet.Attrs {
}
export declare class LabelSet extends TextAnnotation {
    properties: LabelSet.Props;
    constructor(attrs?: Partial<LabelSet.Attrs>);
    static init_LabelSet(): void;
}
