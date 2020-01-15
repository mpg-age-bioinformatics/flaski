import { AbstractSlider, AbstractRangeSliderView } from "./abstract_slider";
import * as p from "../../core/properties";
export declare class RangeSliderView extends AbstractRangeSliderView {
    model: RangeSlider;
}
export declare namespace RangeSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = AbstractSlider.Props;
}
export interface RangeSlider extends RangeSlider.Attrs {
}
export declare class RangeSlider extends AbstractSlider {
    properties: RangeSlider.Props;
    constructor(attrs?: Partial<RangeSlider.Attrs>);
    static init_RangeSlider(): void;
    behaviour: "drag";
    connected: boolean[];
    protected _formatter(value: number, format: string): string;
}
