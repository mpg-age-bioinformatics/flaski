import { Transform } from "./transform";
import { Range } from "../ranges/range";
import { Factor } from "../ranges/factor_range";
import * as p from "../../core/properties";
import { Arrayable } from "../../core/types";
export declare namespace Dodge {
    type Attrs = p.AttrsOf<Props>;
    type Props = Transform.Props & {
        value: p.Property<number>;
        range: p.Property<Range>;
    };
}
export interface Dodge extends Dodge.Attrs {
}
export declare class Dodge extends Transform {
    properties: Dodge.Props;
    constructor(attrs?: Partial<Dodge.Attrs>);
    static init_Dodge(): void;
    v_compute(xs0: Arrayable<number | Factor>): Arrayable<number>;
    compute(x: number | Factor): number;
    protected _compute(x: number): number;
}
