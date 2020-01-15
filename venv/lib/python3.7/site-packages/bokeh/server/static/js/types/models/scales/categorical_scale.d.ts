import { LinearScale } from "./linear_scale";
import { FactorRange } from "../ranges/factor_range";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace CategoricalScale {
    type Attrs = p.AttrsOf<Props>;
    type Props = LinearScale.Props;
}
export interface CategoricalScale extends CategoricalScale.Attrs {
}
export declare class CategoricalScale extends LinearScale {
    properties: CategoricalScale.Props;
    constructor(attrs?: Partial<CategoricalScale.Attrs>);
    source_range: FactorRange;
    compute(x: any): number;
    v_compute(xs: Arrayable<any>): Arrayable<number>;
}
