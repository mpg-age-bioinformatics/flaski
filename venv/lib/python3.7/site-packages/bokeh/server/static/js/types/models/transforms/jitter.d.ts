import { Transform } from "./transform";
import { Range } from "../ranges/range";
import { Factor } from "../ranges/factor_range";
import { Distribution } from "../../core/enums";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace Jitter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Transform.Props & {
        mean: p.Property<number>;
        width: p.Property<number>;
        distribution: p.Property<Distribution>;
        range: p.Property<Range>;
        previous_values: p.Property<Arrayable<number>>;
    };
}
export interface Jitter extends Jitter.Attrs {
}
export declare class Jitter extends Transform {
    properties: Jitter.Props;
    constructor(attrs?: Partial<Jitter.Attrs>);
    static init_Jitter(): void;
    v_compute(xs0: Arrayable<number | Factor>): Arrayable<number>;
    compute(x: number | Factor): number;
    protected _compute(x: number): number;
}
