import { ContinuousColorMapper } from "./continuous_color_mapper";
import { Arrayable } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace LinearColorMapper {
    type Attrs = p.AttrsOf<Props>;
    type Props = ContinuousColorMapper.Props;
}
export interface LinearColorMapper extends LinearColorMapper.Attrs {
}
export declare class LinearColorMapper extends ContinuousColorMapper {
    properties: LinearColorMapper.Props;
    constructor(attrs?: Partial<LinearColorMapper.Attrs>);
    protected _v_compute<T>(data: Arrayable<number>, values: Arrayable<T>, palette: Arrayable<T>, colors: {
        nan_color: T;
        low_color?: T;
        high_color?: T;
    }): void;
}
