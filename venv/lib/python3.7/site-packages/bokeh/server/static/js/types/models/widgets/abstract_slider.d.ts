import * as p from "../../core/properties";
import { Color } from "../../core/types";
import { SliderCallbackPolicy } from "../../core/enums";
import { Control, ControlView } from "./control";
import { CallbackLike0 } from "../callbacks/callback";
export interface SliderSpec {
    start: number;
    end: number;
    value: number[];
    step: number;
}
declare abstract class AbstractBaseSliderView extends ControlView {
    model: AbstractSlider;
    protected group_el: HTMLElement;
    protected slider_el: HTMLElement;
    protected title_el: HTMLElement;
    protected callback_wrapper?: () => void;
    private readonly noUiSlider;
    initialize(): void;
    connect_signals(): void;
    protected _init_callback(): void;
    _update_title(): void;
    protected _set_bar_color(): void;
    protected abstract _calc_to(): SliderSpec;
    protected abstract _calc_from(values: number[]): number | number[];
    protected abstract _set_keypress_handles(): void;
    protected _keypress_handle(e: KeyboardEvent, idx?: 0 | 1): void;
    render(): void;
    protected _slide(values: number[]): void;
    protected _change(values: number[]): void;
}
export declare abstract class AbstractSliderView extends AbstractBaseSliderView {
    protected _calc_to(): SliderSpec;
    protected _calc_from([value]: number[]): number;
    protected _set_keypress_handles(): void;
}
export declare abstract class AbstractRangeSliderView extends AbstractBaseSliderView {
    protected _calc_to(): SliderSpec;
    protected _calc_from(values: number[]): number[];
    protected _set_keypress_handles(): void;
}
export declare namespace AbstractSlider {
    type Attrs = p.AttrsOf<Props>;
    type Props = Control.Props & {
        title: p.Property<string>;
        show_value: p.Property<boolean>;
        start: p.Property<any>;
        end: p.Property<any>;
        value: p.Property<any>;
        value_throttled: p.Property<any>;
        step: p.Property<number>;
        format: p.Property<string>;
        direction: p.Property<"ltr" | "rtl">;
        tooltips: p.Property<boolean>;
        callback: p.Property<CallbackLike0<AbstractSlider> | null>;
        callback_throttle: p.Property<number>;
        callback_policy: p.Property<SliderCallbackPolicy>;
        bar_color: p.Property<Color>;
    };
}
export interface AbstractSlider extends AbstractSlider.Attrs {
}
export declare abstract class AbstractSlider extends Control {
    properties: AbstractSlider.Props;
    constructor(attrs?: Partial<AbstractSlider.Attrs>);
    static init_AbstractSlider(): void;
    behaviour: "drag" | "tap";
    connected: false | boolean[];
    protected _formatter(value: number, _format: string): string;
    pretty(value: number): string;
}
export {};
