import { Filter } from "./filter";
import * as p from "../../core/properties";
import { DataSource } from "../sources/data_source";
export declare namespace CustomJSFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        args: p.Property<{
            [key: string]: unknown;
        }>;
        code: p.Property<string>;
        use_strict: p.Property<boolean>;
    };
}
export interface CustomJSFilter extends CustomJSFilter.Attrs {
}
export declare class CustomJSFilter extends Filter {
    properties: CustomJSFilter.Props;
    constructor(attrs?: Partial<CustomJSFilter.Attrs>);
    static init_CustomJSFilter(): void;
    readonly names: string[];
    readonly values: any[];
    readonly func: Function;
    compute_indices(source: DataSource): number[] | null;
}
