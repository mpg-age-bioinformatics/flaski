import { Transform } from "./transform";
import * as p from "../../core/properties";
import { Arrayable } from "../../core/types";
export declare namespace CustomJSTransform {
    type Attrs = p.AttrsOf<Props>;
    type Props = Transform.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        func: p.Property<string>;
        v_func: p.Property<string>;
        use_strict: p.Property<boolean>;
    };
}
export interface CustomJSTransform extends CustomJSTransform.Attrs {
}
export declare class CustomJSTransform extends Transform {
    properties: CustomJSTransform.Props;
    constructor(attrs?: Partial<CustomJSTransform.Attrs>);
    static init_CustomJSTransform(): void;
    readonly names: string[];
    readonly values: any[];
    protected _make_transform(name: string, func: string): Function;
    readonly scalar_transform: Function;
    readonly vector_transform: Function;
    compute(x: number): number;
    v_compute(xs: Arrayable<number>): Arrayable<number>;
}
