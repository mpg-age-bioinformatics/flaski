"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const signaling_1 = require("./signaling");
const enums = require("./enums");
const array_1 = require("./util/array");
const arrayable_1 = require("./util/arrayable");
const color_1 = require("./util/color");
const types_1 = require("./util/types");
signaling_1.Signal; // XXX: silence TS, because `Signal` appears in declarations due to Signalable
function valueToString(value) {
    try {
        return JSON.stringify(value);
    }
    catch (_a) {
        return value.toString();
    }
}
function isSpec(obj) {
    return types_1.isPlainObject(obj) &&
        ((obj.value === undefined ? 0 : 1) +
            (obj.field === undefined ? 0 : 1) +
            (obj.expr === undefined ? 0 : 1) == 1); // garbage JS XOR
}
exports.isSpec = isSpec;
class Property extends signaling_1.Signalable() {
    constructor(obj, attr, default_value) {
        super();
        this.obj = obj;
        this.attr = attr;
        this.default_value = default_value;
        this.optional = false;
        this.change = new signaling_1.Signal0(this.obj, "change");
        this._init();
        this.connect(this.change, () => this._init());
    }
    update() {
        this._init();
    }
    // ----- customizable policies
    init() { }
    transform(values) {
        return values;
    }
    validate(value) {
        if (!this.valid(value))
            throw new Error(`${this.obj.type}.${this.attr} given invalid value: ${valueToString(value)}`);
    }
    valid(_value) {
        return true;
    }
    // ----- property accessors
    value(do_spec_transform = true) {
        if (this.spec.value === undefined)
            throw new Error("attempted to retrieve property value for property without value specification");
        let ret = this.transform([this.spec.value])[0];
        if (this.spec.transform != null && do_spec_transform)
            ret = this.spec.transform.compute(ret);
        return ret;
    }
    // ----- private methods
    /*protected*/ _init() {
        const obj = this.obj;
        const attr = this.attr;
        let attr_value = obj.getv(attr);
        if (attr_value === undefined) {
            const default_value = this.default_value;
            if (default_value !== undefined)
                attr_value = default_value(obj);
            else
                attr_value = null;
            obj.setv({ [attr]: attr_value }, { silent: true, defaults: true });
        }
        if (types_1.isArray(attr_value))
            this.spec = { value: attr_value };
        else if (isSpec(attr_value))
            this.spec = attr_value;
        else
            this.spec = { value: attr_value };
        //if (this.dataspec && this.spec.field != null && !isString(this.spec.field))
        //  throw new Error(`field value for property '${attr}' is not a string`)
        if (this.spec.value != null)
            this.validate(this.spec.value);
        this.init();
    }
    toString() {
        /*${this.name}*/
        return `Prop(${this.obj}.${this.attr}, spec: ${valueToString(this.spec)})`;
    }
}
exports.Property = Property;
Property.__name__ = "Property";
//
// Primitive Properties
//
class Any extends Property {
}
exports.Any = Any;
Any.__name__ = "Any";
class Array extends Property {
    valid(value) {
        return types_1.isArray(value) || value instanceof Float64Array;
    }
}
exports.Array = Array;
Array.__name__ = "Array";
class Boolean extends Property {
    valid(value) {
        return types_1.isBoolean(value);
    }
}
exports.Boolean = Boolean;
Boolean.__name__ = "Boolean";
class Color extends Property {
    valid(value) {
        return types_1.isString(value) && color_1.is_color(value);
    }
}
exports.Color = Color;
Color.__name__ = "Color";
class Instance extends Property {
}
exports.Instance = Instance;
Instance.__name__ = "Instance";
class Number extends Property {
    valid(value) {
        return types_1.isNumber(value);
    }
}
exports.Number = Number;
Number.__name__ = "Number";
class Int extends Number {
    valid(value) {
        return types_1.isNumber(value) && (value | 0) == value;
    }
}
exports.Int = Int;
Int.__name__ = "Int";
class Angle extends Number {
}
exports.Angle = Angle;
Angle.__name__ = "Angle";
class Percent extends Number {
    valid(value) {
        return types_1.isNumber(value) && 0 <= value && value <= 1.0;
    }
}
exports.Percent = Percent;
Percent.__name__ = "Percent";
class String extends Property {
    valid(value) {
        return types_1.isString(value);
    }
}
exports.String = String;
String.__name__ = "String";
class FontSize extends String {
}
exports.FontSize = FontSize;
FontSize.__name__ = "FontSize";
class Font extends String {
} // TODO (bev) don't think this exists python side
exports.Font = Font;
Font.__name__ = "Font";
//
// Enum properties
//
class EnumProperty extends Property {
    valid(value) {
        return types_1.isString(value) && array_1.includes(this.enum_values, value);
    }
}
exports.EnumProperty = EnumProperty;
EnumProperty.__name__ = "EnumProperty";
function Enum(values) {
    return class extends EnumProperty {
        get enum_values() {
            return values;
        }
    };
}
exports.Enum = Enum;
class Direction extends EnumProperty {
    get enum_values() {
        return enums.Direction;
    }
    transform(values) {
        const result = new Uint8Array(values.length);
        for (let i = 0; i < values.length; i++) {
            switch (values[i]) {
                case "clock":
                    result[i] = 0;
                    break;
                case "anticlock":
                    result[i] = 1;
                    break;
            }
        }
        return result;
    }
}
exports.Direction = Direction;
Direction.__name__ = "Direction";
exports.Anchor = Enum(enums.Anchor);
exports.AngleUnits = Enum(enums.AngleUnits);
exports.BoxOrigin = Enum(enums.BoxOrigin);
exports.ButtonType = Enum(enums.ButtonType);
exports.Dimension = Enum(enums.Dimension);
exports.Dimensions = Enum(enums.Dimensions);
exports.Distribution = Enum(enums.Distribution);
exports.FontStyle = Enum(enums.FontStyle);
exports.HatchPatternType = Enum(enums.HatchPatternType);
exports.HTTPMethod = Enum(enums.HTTPMethod);
exports.HexTileOrientation = Enum(enums.HexTileOrientation);
exports.HoverMode = Enum(enums.HoverMode);
exports.LatLon = Enum(enums.LatLon);
exports.LegendClickPolicy = Enum(enums.LegendClickPolicy);
exports.LegendLocation = Enum(enums.LegendLocation);
exports.LineCap = Enum(enums.LineCap);
exports.LineJoin = Enum(enums.LineJoin);
exports.LinePolicy = Enum(enums.LinePolicy);
exports.Location = Enum(enums.Location);
exports.Logo = Enum(enums.Logo);
exports.MarkerType = Enum(enums.MarkerType);
exports.Orientation = Enum(enums.Orientation);
exports.OutputBackend = Enum(enums.OutputBackend);
exports.PaddingUnits = Enum(enums.PaddingUnits);
exports.Place = Enum(enums.Place);
exports.PointPolicy = Enum(enums.PointPolicy);
exports.RadiusDimension = Enum(enums.RadiusDimension);
exports.RenderLevel = Enum(enums.RenderLevel);
exports.RenderMode = Enum(enums.RenderMode);
exports.ResetPolicy = Enum(enums.ResetPolicy);
exports.RoundingFunction = Enum(enums.RoundingFunction);
exports.Side = Enum(enums.Side);
exports.SizingMode = Enum(enums.SizingMode);
exports.SliderCallbackPolicy = Enum(enums.SliderCallbackPolicy);
exports.Sort = Enum(enums.Sort);
exports.SpatialUnits = Enum(enums.SpatialUnits);
exports.StartEnd = Enum(enums.StartEnd);
exports.StepMode = Enum(enums.StepMode);
exports.TapBehavior = Enum(enums.TapBehavior);
exports.TextAlign = Enum(enums.TextAlign);
exports.TextBaseline = Enum(enums.TextBaseline);
exports.TextureRepetition = Enum(enums.TextureRepetition);
exports.TickLabelOrientation = Enum(enums.TickLabelOrientation);
exports.TooltipAttachment = Enum(enums.TooltipAttachment);
exports.UpdateMode = Enum(enums.UpdateMode);
exports.VerticalAlign = Enum(enums.VerticalAlign);
//
// DataSpec properties
//
class ScalarSpec extends Property {
}
exports.ScalarSpec = ScalarSpec;
ScalarSpec.__name__ = "ScalarSpec";
class VectorSpec extends Property {
    array(source) {
        let ret;
        if (this.spec.field != null) {
            ret = this.transform(source.get_column(this.spec.field));
            if (ret == null)
                throw new Error(`attempted to retrieve property array for nonexistent field '${this.spec.field}'`);
        }
        else if (this.spec.expr != null) {
            ret = this.transform(this.spec.expr.v_compute(source));
        }
        else {
            let length = source.get_length();
            if (length == null)
                length = 1;
            const value = this.value(false); // don't apply any spec transform
            ret = array_1.repeat(value, length);
        }
        if (this.spec.transform != null)
            ret = this.spec.transform.v_compute(ret);
        return ret;
    }
}
exports.VectorSpec = VectorSpec;
VectorSpec.__name__ = "VectorSpec";
class DataSpec extends VectorSpec {
}
exports.DataSpec = DataSpec;
DataSpec.__name__ = "DataSpec";
class UnitsSpec extends VectorSpec {
    init() {
        if (this.spec.units == null)
            this.spec.units = this.default_units;
        const units = this.spec.units;
        if (!array_1.includes(this.valid_units, units))
            throw new Error(`units must be one of ${this.valid_units.join(", ")}; got: ${units}`);
    }
    get units() {
        return this.spec.units;
    }
    set units(units) {
        this.spec.units = units;
    }
}
exports.UnitsSpec = UnitsSpec;
UnitsSpec.__name__ = "UnitsSpec";
class AngleSpec extends UnitsSpec {
    get default_units() { return "rad"; }
    get valid_units() { return enums.AngleUnits; }
    transform(values) {
        if (this.spec.units == "deg")
            values = arrayable_1.map(values, (x) => x * Math.PI / 180.0);
        values = arrayable_1.map(values, (x) => -x);
        return super.transform(values);
    }
}
exports.AngleSpec = AngleSpec;
AngleSpec.__name__ = "AngleSpec";
class BooleanSpec extends DataSpec {
}
exports.BooleanSpec = BooleanSpec;
BooleanSpec.__name__ = "BooleanSpec";
class ColorSpec extends DataSpec {
}
exports.ColorSpec = ColorSpec;
ColorSpec.__name__ = "ColorSpec";
class CoordinateSpec extends DataSpec {
}
exports.CoordinateSpec = CoordinateSpec;
CoordinateSpec.__name__ = "CoordinateSpec";
class CoordinateSeqSpec extends DataSpec {
}
exports.CoordinateSeqSpec = CoordinateSeqSpec;
CoordinateSeqSpec.__name__ = "CoordinateSeqSpec";
class DistanceSpec extends UnitsSpec {
    get default_units() { return "data"; }
    get valid_units() { return enums.SpatialUnits; }
}
exports.DistanceSpec = DistanceSpec;
DistanceSpec.__name__ = "DistanceSpec";
class FontSizeSpec extends DataSpec {
}
exports.FontSizeSpec = FontSizeSpec;
FontSizeSpec.__name__ = "FontSizeSpec";
class MarkerSpec extends DataSpec {
}
exports.MarkerSpec = MarkerSpec;
MarkerSpec.__name__ = "MarkerSpec";
class NumberSpec extends DataSpec {
}
exports.NumberSpec = NumberSpec;
NumberSpec.__name__ = "NumberSpec";
class StringSpec extends DataSpec {
}
exports.StringSpec = StringSpec;
StringSpec.__name__ = "StringSpec";
class NullStringSpec extends DataSpec {
}
exports.NullStringSpec = NullStringSpec;
NullStringSpec.__name__ = "NullStringSpec";
