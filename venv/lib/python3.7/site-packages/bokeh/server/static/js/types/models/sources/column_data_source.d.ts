import { ColumnarDataSource } from "./columnar_data_source";
import { Arrayable, Data } from "../../core/types";
import * as p from "../../core/properties";
import { Set } from "../../core/util/data_structures";
import { Shape } from "../../core/util/serialization";
export declare function stream_to_column(col: Arrayable, new_col: Arrayable, rollover?: number): Arrayable;
export declare type Slice = {
    start?: number;
    stop?: number;
    step?: number;
};
export declare function slice(ind: number | Slice, length: number): [number, number, number];
export declare type Patch = [number, unknown] | [[number, number | Slice] | [number, number | Slice, number | Slice], unknown[]] | [Slice, unknown[]];
export declare type PatchSet = {
    [key: string]: Patch[];
};
export declare function patch_to_column(col: Arrayable, patch: Patch[], shapes: Shape[]): Set<number>;
export declare namespace ColumnDataSource {
    type Attrs = p.AttrsOf<Props>;
    type Props = ColumnarDataSource.Props & {
        data: p.Property<{
            [key: string]: Arrayable;
        }>;
    };
}
export interface ColumnDataSource extends ColumnDataSource.Attrs {
}
export declare class ColumnDataSource extends ColumnarDataSource {
    properties: ColumnDataSource.Props;
    constructor(attrs?: Partial<ColumnDataSource.Attrs>);
    static init_ColumnDataSource(): void;
    initialize(): void;
    attributes_as_json(include_defaults?: boolean, value_to_json?: typeof ColumnDataSource._value_to_json): any;
    static _value_to_json(key: string, value: any, optional_parent_object: any): any;
    stream(new_data: Data, rollover?: number, setter_id?: string): void;
    patch(patches: PatchSet, setter_id?: string): void;
}
