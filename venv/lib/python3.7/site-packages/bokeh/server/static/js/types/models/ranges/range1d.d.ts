import { Range } from "./range";
import * as p from "../../core/properties";
export declare namespace Range1d {
    type Attrs = p.AttrsOf<Props>;
    type Props = Range.Props & {
        start: p.Property<number>;
        end: p.Property<number>;
        reset_start: p.Property<number>;
        reset_end: p.Property<number>;
    };
}
export interface Range1d extends Range1d.Attrs {
}
export declare class Range1d extends Range {
    properties: Range1d.Props;
    constructor(attrs?: Partial<Range1d.Attrs>);
    static init_Range1d(): void;
    protected _set_auto_bounds(): void;
    initialize(): void;
    readonly min: number;
    readonly max: number;
    reset(): void;
}
