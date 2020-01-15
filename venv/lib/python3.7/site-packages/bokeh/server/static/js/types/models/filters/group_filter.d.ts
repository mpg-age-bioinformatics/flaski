import { Filter } from "./filter";
import * as p from "../../core/properties";
import { ColumnarDataSource } from "../sources/columnar_data_source";
export declare namespace GroupFilter {
    type Attrs = p.AttrsOf<Props>;
    type Props = Filter.Props & {
        column_name: p.Property<string>;
        group: p.Property<string>;
    };
}
export interface GroupFilter extends GroupFilter.Attrs {
}
export declare class GroupFilter extends Filter {
    properties: GroupFilter.Props;
    constructor(attrs?: Partial<GroupFilter.Attrs>);
    static init_GroupFilter(): void;
    indices: number[] | null;
    compute_indices(source: ColumnarDataSource): number[] | null;
}
