import { Annotation, AnnotationView } from "./annotation";
import { ColumnarDataSource } from "../sources/columnar_data_source";
import { ArrowHead } from "./arrow_head";
import { LineVector } from "../../core/property_mixins";
import { Line } from "../../core/visuals";
import { Arrayable } from "../../core/types";
import { Dimension } from "../../core/enums";
import * as p from "../../core/properties";
export declare class WhiskerView extends AnnotationView {
    model: Whisker;
    visuals: Whisker.Visuals;
    protected _lower: Arrayable<number>;
    protected _upper: Arrayable<number>;
    protected _base: Arrayable<number>;
    protected max_lower: number;
    protected max_upper: number;
    protected max_base: number;
    protected _lower_sx: Arrayable<number>;
    protected _lower_sy: Arrayable<number>;
    protected _upper_sx: Arrayable<number>;
    protected _upper_sy: Arrayable<number>;
    initialize(): void;
    connect_signals(): void;
    set_data(source: ColumnarDataSource): void;
    protected _map_data(): void;
    render(): void;
}
export declare namespace Whisker {
    type Attrs = p.AttrsOf<Props>;
    type Props = Annotation.Props & LineVector & {
        lower: p.DistanceSpec;
        lower_head: p.Property<ArrowHead>;
        upper: p.DistanceSpec;
        upper_head: p.Property<ArrowHead>;
        base: p.DistanceSpec;
        dimension: p.Property<Dimension>;
        source: p.Property<ColumnarDataSource>;
        x_range_name: p.Property<string>;
        y_range_name: p.Property<string>;
    };
    type Visuals = Annotation.Visuals & {
        line: Line;
    };
}
export interface Whisker extends Whisker.Attrs {
}
export declare class Whisker extends Annotation {
    properties: Whisker.Props;
    constructor(attrs?: Partial<Whisker.Attrs>);
    static init_Whisker(): void;
}
