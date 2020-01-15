import { Model } from "../../model";
import { Selection } from "../selections/selection";
import { CallbackLike0 } from "../callbacks/callback";
import * as p from "../../core/properties";
export declare namespace DataSource {
    type Attrs = p.AttrsOf<Props>;
    type Props = Model.Props & {
        selected: p.Property<Selection>;
        callback: p.Property<CallbackLike0<DataSource> | null>;
    };
}
export interface DataSource extends DataSource.Attrs {
}
export declare abstract class DataSource extends Model {
    properties: DataSource.Props;
    constructor(attrs?: Partial<DataSource.Attrs>);
    static init_DataSource(): void;
    connect_signals(): void;
    setup?(): void;
}
