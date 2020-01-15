import { Signal0, Signal } from "./signaling";
import { HasProps } from "./has_props";
import * as enums from "./enums";
import { Arrayable, Color as ColorType } from "./types";
import { Factor } from "../models/ranges/factor_range";
import { ColumnarDataSource } from "../models/sources/columnar_data_source";
import { Scalar, Vector, Dimensional } from "./vectorization";
export declare function isSpec(obj: any): boolean;
export declare type AttrsOf<P> = {
    [K in keyof P]: P[K] extends Property<infer T> ? T : never;
};
export declare type DefineOf<P> = {
    [K in keyof P]: P[K] extends Property<infer T> ? [PropertyConstructor<T>, (T | (() => T))?] : never;
};
export interface PropertyConstructor<T> {
    new (obj: HasProps, attr: string, default_value?: (obj: HasProps) => T): Property<T>;
    readonly prototype: Property<T>;
}
declare const Property_base: {
    new (): {
        connect<Args, Sender extends object>(signal: Signal<Args, Sender>, slot: import("./signaling").Slot<Args, Sender>): boolean;
        disconnect<Args_1, Sender_1 extends object>(signal: Signal<Args_1, Sender_1>, slot: import("./signaling").Slot<Args_1, Sender_1>): boolean;
    };
};
export declare abstract class Property<T> extends Property_base {
    readonly obj: HasProps;
    readonly attr: string;
    readonly default_value?: ((obj: HasProps) => T) | undefined;
    __value__: T;
    spec: {
        value?: any;
        field?: string;
        expr?: any;
        transform?: any;
        units?: any;
    };
    optional: boolean;
    readonly change: Signal0<HasProps>;
    constructor(obj: HasProps, attr: string, default_value?: ((obj: HasProps) => T) | undefined);
    update(): void;
    init(): void;
    transform(values: any): any;
    validate(value: any): void;
    valid(_value: unknown): boolean;
    value(do_spec_transform?: boolean): any;
    _init(): void;
    toString(): string;
}
export declare class Any extends Property<any> {
}
export declare class Array extends Property<any[]> {
    valid(value: unknown): boolean;
}
export declare class Boolean extends Property<boolean> {
    valid(value: unknown): boolean;
}
export declare class Color extends Property<ColorType> {
    valid(value: unknown): boolean;
}
export declare class Instance extends Property<any> {
}
export declare class Number extends Property<number> {
    valid(value: unknown): boolean;
}
export declare class Int extends Number {
    valid(value: unknown): boolean;
}
export declare class Angle extends Number {
}
export declare class Percent extends Number {
    valid(value: unknown): boolean;
}
export declare class String extends Property<string> {
    valid(value: unknown): boolean;
}
export declare class FontSize extends String {
}
export declare class Font extends String {
}
export declare abstract class EnumProperty<T extends string> extends Property<T> {
    readonly enum_values: T[];
    valid(value: unknown): boolean;
}
export declare function Enum<T extends string>(values: T[]): PropertyConstructor<T>;
export declare class Direction extends EnumProperty<enums.Direction> {
    readonly enum_values: enums.Direction[];
    transform(values: any): any;
}
export declare const Anchor: PropertyConstructor<enums.Anchor>;
export declare const AngleUnits: PropertyConstructor<enums.AngleUnits>;
export declare const BoxOrigin: PropertyConstructor<enums.BoxOrigin>;
export declare const ButtonType: PropertyConstructor<enums.ButtonType>;
export declare const Dimension: PropertyConstructor<enums.Dimension>;
export declare const Dimensions: PropertyConstructor<enums.Dimensions>;
export declare const Distribution: PropertyConstructor<enums.Distribution>;
export declare const FontStyle: PropertyConstructor<enums.FontStyle>;
export declare const HatchPatternType: PropertyConstructor<enums.HatchPatternType>;
export declare const HTTPMethod: PropertyConstructor<enums.HTTPMethod>;
export declare const HexTileOrientation: PropertyConstructor<enums.HexTileOrientation>;
export declare const HoverMode: PropertyConstructor<enums.HoverMode>;
export declare const LatLon: PropertyConstructor<enums.LatLon>;
export declare const LegendClickPolicy: PropertyConstructor<enums.LegendClickPolicy>;
export declare const LegendLocation: PropertyConstructor<enums.Anchor>;
export declare const LineCap: PropertyConstructor<enums.LineCap>;
export declare const LineJoin: PropertyConstructor<enums.LineJoin>;
export declare const LinePolicy: PropertyConstructor<enums.LinePolicy>;
export declare const Location: PropertyConstructor<enums.Location>;
export declare const Logo: PropertyConstructor<enums.Logo>;
export declare const MarkerType: PropertyConstructor<enums.MarkerType>;
export declare const Orientation: PropertyConstructor<enums.Orientation>;
export declare const OutputBackend: PropertyConstructor<enums.OutputBackend>;
export declare const PaddingUnits: PropertyConstructor<enums.PaddingUnits>;
export declare const Place: PropertyConstructor<enums.Place>;
export declare const PointPolicy: PropertyConstructor<enums.PointPolicy>;
export declare const RadiusDimension: PropertyConstructor<enums.RadiusDimension>;
export declare const RenderLevel: PropertyConstructor<enums.RenderLevel>;
export declare const RenderMode: PropertyConstructor<enums.RenderMode>;
export declare const ResetPolicy: PropertyConstructor<enums.ResetPolicy>;
export declare const RoundingFunction: PropertyConstructor<enums.RoundingFunction>;
export declare const Side: PropertyConstructor<enums.Location>;
export declare const SizingMode: PropertyConstructor<enums.SizingMode>;
export declare const SliderCallbackPolicy: PropertyConstructor<enums.SliderCallbackPolicy>;
export declare const Sort: PropertyConstructor<enums.Sort>;
export declare const SpatialUnits: PropertyConstructor<enums.SpatialUnits>;
export declare const StartEnd: PropertyConstructor<enums.StartEnd>;
export declare const StepMode: PropertyConstructor<enums.StepMode>;
export declare const TapBehavior: PropertyConstructor<enums.TapBehavior>;
export declare const TextAlign: PropertyConstructor<enums.TextAlign>;
export declare const TextBaseline: PropertyConstructor<enums.TextBaseline>;
export declare const TextureRepetition: PropertyConstructor<enums.TextureRepetition>;
export declare const TickLabelOrientation: PropertyConstructor<enums.TickLabelOrientation>;
export declare const TooltipAttachment: PropertyConstructor<enums.TooltipAttachment>;
export declare const UpdateMode: PropertyConstructor<enums.UpdateMode>;
export declare const VerticalAlign: PropertyConstructor<enums.VerticalAlign>;
export declare abstract class ScalarSpec<T, S extends Scalar<T> = Scalar<T>> extends Property<T | S> {
    __value__: T;
    __scalar__: S;
}
export declare abstract class VectorSpec<T, V extends Vector<T> = Vector<T>> extends Property<T | V> {
    __value__: T;
    __vector__: V;
    array(source: ColumnarDataSource): any[];
}
export declare abstract class DataSpec<T> extends VectorSpec<T> {
}
export declare abstract class UnitsSpec<T, Units> extends VectorSpec<T, Dimensional<Vector<T>, Units>> {
    readonly default_units: Units;
    readonly valid_units: Units[];
    init(): void;
    units: Units;
}
export declare class AngleSpec extends UnitsSpec<number, enums.AngleUnits> {
    readonly default_units: enums.AngleUnits;
    readonly valid_units: enums.AngleUnits[];
    transform(values: Arrayable): Arrayable;
}
export declare class BooleanSpec extends DataSpec<boolean> {
}
export declare class ColorSpec extends DataSpec<ColorType | null> {
}
export declare class CoordinateSpec extends DataSpec<number | Factor> {
}
export declare class CoordinateSeqSpec extends DataSpec<number[] | Factor[]> {
}
export declare class DistanceSpec extends UnitsSpec<number, enums.SpatialUnits> {
    readonly default_units: enums.SpatialUnits;
    readonly valid_units: enums.SpatialUnits[];
}
export declare class FontSizeSpec extends DataSpec<string> {
}
export declare class MarkerSpec extends DataSpec<string> {
}
export declare class NumberSpec extends DataSpec<number> {
}
export declare class StringSpec extends DataSpec<string> {
}
export declare class NullStringSpec extends DataSpec<string | null> {
}
export {};
