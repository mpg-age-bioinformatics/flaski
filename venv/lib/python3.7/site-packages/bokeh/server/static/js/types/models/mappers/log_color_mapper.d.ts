import { ContinuousColorMapper } from "./continuous_color_mapper";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace LogColorMapper {
    type Attrs = p.AttrsOf<Props>;
    type Props = ContinuousColorMapper.Props;
}
export interface LogColorMapper extends LogColorMapper.Attrs {
}
export declare class LogColorMapper extends ContinuousColorMapper {
    properties: LogColorMapper.Props;
    constructor(attrs?: Partial<LogColorMapper.Attrs>);
    protected _v_compute<T>(data: Arrayable<number>, values: Arrayable<T>, palette: Arrayable<T>, colors: {
        nan_color: T;
        low_color?: T;
        high_color?: T;
    }): void;
}
