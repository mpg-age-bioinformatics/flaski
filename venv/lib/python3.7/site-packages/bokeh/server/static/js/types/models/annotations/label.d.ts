import { TextAnnotation, TextAnnotationView } from "./text_annotation";
import { SpatialUnits, AngleUnits } from "../../core/enums";
import { Size } from "../../core/layout";
import * as mixins from "../../core/property_mixins";
import * as p from "../../core/properties";
export declare class LabelView extends TextAnnotationView {
    model: Label;
    visuals: Label.Visuals;
    initialize(): void;
    protected _get_size(): Size;
    render(): void;
}
export declare namespace Label {
    type Props = TextAnnotation.Props & {
        x: p.Property<number>;
        x_units: p.Property<SpatialUnits>;
        y: p.Property<number>;
        y_units: p.Property<SpatialUnits>;
        text: p.Property<string>;
        angle: p.Property<number>;
        angle_units: p.Property<AngleUnits>;
        x_offset: p.Property<number>;
        y_offset: p.Property<number>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
    } & mixins.TextScalar & mixins.BorderLine & mixins.BackgroundFill;
    type Attrs = p.AttrsOf<Props>;
    type Visuals = TextAnnotation.Visuals;
}
export interface Label extends Label.Attrs {
}
export declare class Label extends TextAnnotation {
    properties: Label.Props;
    constructor(attrs?: Partial<Label.Attrs>);
    static init_Label(): void;
}
