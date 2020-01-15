import { Scale } from "./scale";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace LogScale {
    type Attrs = p.AttrsOf<Props>;
    type Props = Scale.Props;
}
export interface LogScale extends LogScale.Attrs {
}
export declare class LogScale extends Scale {
    properties: LogScale.Props;
    constructor(attrs?: Partial<LogScale.Attrs>);
    compute(x: number): number;
    v_compute(xs: Arrayable<number>): Arrayable<number>;
    invert(xprime: number): number;
    v_invert(xprimes: Arrayable<number>): Arrayable<number>;
    protected _get_safe_factor(orig_start: number, orig_end: number): [number, number];
    _compute_state(): [number, number, number, number];
}
