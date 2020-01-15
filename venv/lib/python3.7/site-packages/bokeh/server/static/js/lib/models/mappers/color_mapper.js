"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const mapper_1 = require("./mapper");
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
const color_1 = require("../../core/util/color");
const compat_1 = require("../../core/util/compat");
function _convert_color(color) {
    if (types_1.isNumber(color))
        return color;
    if (color[0] != "#")
        color = color_1.color2hex(color);
    if (color.length != 9)
        color = color + 'ff';
    return parseInt(color.slice(1), 16);
}
exports._convert_color = _convert_color;
function _convert_palette(palette) {
    const new_palette = new Uint32Array(palette.length);
    for (let i = 0, end = palette.length; i < end; i++)
        new_palette[i] = _convert_color(palette[i]);
    return new_palette;
}
exports._convert_palette = _convert_palette;
function _uint32_to_rgba(values) {
    if (compat_1.is_little_endian) {
        const view = new DataView(values.buffer);
        for (let i = 0, end = values.length; i < end; i++)
            view.setUint32(i * 4, values[i]);
    }
    return new Uint8Array(values.buffer);
}
exports._uint32_to_rgba = _uint32_to_rgba;
class ColorMapper extends mapper_1.Mapper {
    constructor(attrs) {
        super(attrs);
    }
    static init_ColorMapper() {
        this.define({
            palette: [p.Any],
            nan_color: [p.Color, "gray"],
        });
    }
    v_compute(xs) {
        const values = new Array(xs.length);
        this._v_compute(xs, values, this.palette, this._colors((c) => c));
        return values;
    }
    get rgba_mapper() {
        const self = this;
        const palette = _convert_palette(this.palette);
        const colors = this._colors(_convert_color);
        return {
            v_compute(xs) {
                const values = new Uint32Array(xs.length);
                self._v_compute(xs, values, palette, colors);
                return _uint32_to_rgba(values);
            },
        };
    }
    _colors(conv) {
        return { nan_color: conv(this.nan_color) };
    }
}
exports.ColorMapper = ColorMapper;
ColorMapper.__name__ = "ColorMapper";
ColorMapper.init_ColorMapper();
