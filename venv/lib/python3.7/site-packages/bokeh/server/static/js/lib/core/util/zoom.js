"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const math_1 = require("./math");
// Module for zoom-related functions
function scale_highlow(range, factor, center) {
    const [low, high] = [range.start, range.end];
    const x = center != null ? center : (high + low) / 2.0;
    const x0 = low - (low - x) * factor;
    const x1 = high - (high - x) * factor;
    return [x0, x1];
}
exports.scale_highlow = scale_highlow;
function get_info(scales, [sxy0, sxy1]) {
    const info = {};
    for (const name in scales) {
        const scale = scales[name];
        const [start, end] = scale.r_invert(sxy0, sxy1);
        info[name] = { start, end };
    }
    return info;
}
exports.get_info = get_info;
function scale_range(frame, factor, h_axis = true, v_axis = true, center) {
    /*
     * Utility function for zoom tools to calculate/create the zoom_info object
     * of the form required by ``PlotView.update_range``
     *
     * Parameters:
     *   frame : CartesianFrame
     *   factor : Number
     *   h_axis : Boolean, optional
     *     whether to zoom the horizontal axis (default = true)
     *   v_axis : Boolean, optional
     *     whether to zoom the horizontal axis (default = true)
     *   center : object, optional
     *     of form {'x': Number, 'y', Number}
     *
     * Returns:
     *   object:
     */
    // clamp the  magnitude of factor, if it is > 1 bad things happen
    factor = math_1.clamp(factor, -0.9, 0.9);
    const hfactor = h_axis ? factor : 0;
    const [sx0, sx1] = scale_highlow(frame.bbox.h_range, hfactor, center != null ? center.x : undefined);
    const xrs = get_info(frame.xscales, [sx0, sx1]);
    const vfactor = v_axis ? factor : 0;
    const [sy0, sy1] = scale_highlow(frame.bbox.v_range, vfactor, center != null ? center.y : undefined);
    const yrs = get_info(frame.yscales, [sy0, sy1]);
    // OK this sucks we can't set factor independently in each direction. It is used
    // for GMap plots, and GMap plots always preserve aspect, so effective the value
    // of 'dimensions' is ignored.
    return { xrs, yrs, factor };
}
exports.scale_range = scale_range;
