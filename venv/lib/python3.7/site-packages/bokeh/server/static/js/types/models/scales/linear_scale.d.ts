import { Scale } from "./scale";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace LinearScale {
    type Attrs = p.AttrsOf<Props>;
    type Props = Scale.Props;
}
export interface LinearScale extends LinearScale.Attrs {
}
export declare class LinearScale extends Scale {
    properties: LinearScale.Props;
    constructor(attrs?: Partial<LinearScale.Attrs>);
    compute(x: number): number;
    v_compute(xs: Arrayable<number>): Arrayable<number>;
    invert(xprime: number): number;
    v_invert(xprimes: Arrayable<number>): Arrayable<number>;
    _compute_state(): [number, number];
}
