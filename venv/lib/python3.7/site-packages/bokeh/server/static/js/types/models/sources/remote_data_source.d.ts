import { WebDataSource } from "./web_data_source";
import * as p from "../../core/properties";
import { Arrayable } from "../../core/types";
export declare namespace RemoteDataSource {
    type Attrs = p.AttrsOf<Props>;
    type Props = WebDataSource.Props & {
        polling_interval: p.Property<number>;
    };
}
export interface RemoteDataSource extends RemoteDataSource.Attrs {
}
export declare abstract class RemoteDataSource extends WebDataSource {
    properties: RemoteDataSource.Props;
    constructor(attrs?: Partial<RemoteDataSource.Attrs>);
    get_column(colname: string): Arrayable;
    abstract setup(): void;
    initialize(): void;
    static init_RemoteDataSource(): void;
}
