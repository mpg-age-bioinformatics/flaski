import { Model } from "../../model";
import { Plot } from "../plots/plot";
import { CustomJS } from "../callbacks/customjs";
import * as p from "../../core/properties";
export declare namespace Range {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        bounds: p.Property<[number, number] | "auto" | null>;
        min_interval: p.Property<number>;
        max_interval: p.Property<number>;
        callback: p.Property<((obj: Range) => void) | CustomJS>;
        plots: p.Property<Plot[]>;
    };
}
export interface Range extends Range.Attrs {
}
export declare abstract class Range extends Model {
    properties: Range.Props;
    constructor(attrs?: Partial<Range.Attrs>);
    static init_Range(): void;
    start: number;
    end: number;
    min: number;
    max: number;
    have_updated_interactively: boolean;
    connect_signals(): void;
    abstract reset(): void;
    protected _emit_callback(): void;
    readonly is_reversed: boolean;
}
