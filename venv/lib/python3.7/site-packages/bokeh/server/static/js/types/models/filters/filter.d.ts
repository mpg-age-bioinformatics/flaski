import { Model } from "../../model";
import { DataSource } from "../sources/data_source";
import * as p from "../../core/properties";
export declare namespace Filter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        filter: p.Property<boolean[] | number[] | null>;
    };
}
export interface Filter extends Filter.Attrs {
}
export declare class Filter extends Model {
    properties: Filter.Props;
    constructor(attrs?: Partial<Filter.Attrs>);
    static init_Filter(): void;
    compute_indices(_source: DataSource): number[] | null;
}
