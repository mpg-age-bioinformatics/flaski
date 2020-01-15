import { ColorMapper } from "./color_mapper";
import { Arrayable, Color } from "../../core/types";
import * as p from "../../core/properties";
export declare namespace ContinuousColorMapper {
    type Attrs = p.AttrsOf<Props>;
    type Props = ColorMapper.Props & {
        high: p.Property<number>;
        low: p.Property<number>;
        high_color: p.Property<Color>;
        low_color: p.Property<Color>;
    };
}
export interface ContinuousColorMapper extends ContinuousColorMapper.Attrs {
}
export declare abstract class ContinuousColorMapper extends ColorMapper {
    properties: ContinuousColorMapper.Props;
    constructor(attrs?: Partial<ContinuousColorMapper.Attrs>);
    static init_ContinuousColorMapper(): void;
    protected _colors<T>(conv: (c: Color) => T): {
        nan_color: T;
        low_color?: T;
        high_color?: T;
    };
    protected abstract _v_compute<T>(data: Arrayable<number>, values: Arrayable<T>, palette: Arrayable<T>, colors: {
        nan_color: T;
        low_color?: T;
        high_color?: T;
    }): void;
}
