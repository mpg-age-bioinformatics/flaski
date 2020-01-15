"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const continuous_color_mapper_1 = require("./continuous_color_mapper");
const arrayable_1 = require("../../core/util/arrayable");
// Math.log1p() is not supported by any version of IE, so let's use a polyfill based on
// https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Math/log1p.
const log1p = Math.log1p != null ? Math.log1p : (x) => Math.log(1 + x);
class LogColorMapper extends continuous_color_mapper_1.ContinuousColorMapper {
    constructor(attrs) {
        super(attrs);
    }
    _v_compute(data, values, palette, colors) {
        const { nan_color, low_color, high_color } = colors;
        const n = palette.length;
        const low = this.low != null ? this.low : arrayable_1.min(data);
        const high = this.high != null ? this.high : arrayable_1.max(data);
        const scale = n / (log1p(high) - log1p(low)); // subtract the low offset
        const max_key = palette.length - 1;
        for (let i = 0, end = data.length; i < end; i++) {
            const d = data[i];
            // Check NaN
            if (isNaN(d)) {
                values[i] = nan_color;
                continue;
            }
            if (d > high) {
                values[i] = high_color != null ? high_color : palette[max_key];
                continue;
            }
            // This handles the edge case where d == high, since the code below maps
            // values exactly equal to high to palette.length, which is greater than
            // max_key
            if (d == high) {
                values[i] = palette[max_key];
                continue;
            }
            if (d < low) {
                values[i] = low_color != null ? low_color : palette[0];
                continue;
            }
            // Get the key
            const log = log1p(d) - log1p(low); // subtract the low offset
            let key = Math.floor(log * scale);
            // Deal with upper bound
            if (key > max_key)
                key = max_key;
            values[i] = palette[key];
        }
    }
}
exports.LogColorMapper = LogColorMapper;
LogColorMapper.__name__ = "LogColorMapper";
