import { Filter } from "./filter";
import * as p from "../../core/properties";
import { DataSource } from "../sources/data_source";
export declare namespace IndexFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        indices: p.Property<number[] | null>;
    };
}
export interface IndexFilter extends IndexFilter.Attrs {
}
export declare class IndexFilter extends Filter {
    properties: IndexFilter.Props;
    constructor(attrs?: Partial<IndexFilter.Attrs>);
    static init_IndexFilter(): void;
    compute_indices(_source: DataSource): number[] | null;
}
