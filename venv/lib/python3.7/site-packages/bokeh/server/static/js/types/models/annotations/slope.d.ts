import { Annotation, AnnotationView } from "./annotation";
import { LineScalar } from "../../core/property_mixins";
import { Line } from "../../core/visuals";
import { Color } from "../../core/types";
import * as p from "../../core/properties";
export declare class SlopeView extends AnnotationView {
    model: Slope;
    visuals: Slope.Visuals;
    initialize(): void;
    connect_signals(): void;
    render(): void;
    protected _draw_slope(): void;
}
export declare namespace Slope {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & LineScalar & {
        gradient: p.Property<number | null>;
        y_intercept: p.Property<number | null>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
        line_color: p.Property<Color>;
        line_width: p.Property<number>;
        line_alpha: p.Property<number>;
    };
    type Visuals = Annotation.Visuals & {
        line: Line;
    };
}
export interface Slope extends Slope.Attrs {
}
export declare class Slope extends Annotation {
    properties: Slope.Props;
    constructor(attrs?: Partial<Slope.Attrs>);
    static init_Slope(): void;
}
