import { Annotation, AnnotationView } from "./annotation";
import { LineScalar } from "../../core/property_mixins";
import { Line } from "../../core/visuals";
import { SpatialUnits, RenderMode, Dimension } from "../../core/enums";
import * as p from "../../core/properties";
export declare class SpanView extends AnnotationView {
    model: Span;
    visuals: Span.Visuals;
    initialize(): void;
    connect_signals(): void;
    render(): void;
    protected _draw_span(): void;
}
export declare namespace Span {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & LineScalar & {
        render_mode: p.Property<RenderMode>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
        location: p.Property<number | null>;
        location_units: p.Property<SpatialUnits>;
        dimension: p.Property<Dimension>;
        for_hover: p.Property<boolean>;
        computed_location: p.Property<number | null>;
    };
    type Visuals = Annotation.Visuals & {
        line: Line;
    };
}
export interface Span extends Span.Attrs {
}
export declare class Span extends Annotation {
    properties: Span.Props;
    constructor(attrs?: Partial<Span.Attrs>);
    static init_Span(): void;
}
