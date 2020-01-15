"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const proj4 = require("proj4/lib/core");
const Projection = require("proj4/lib/Proj");
const mercator = new Projection('GOOGLE');
const wgs84 = new Projection('WGS84');
exports.wgs84_mercator = proj4(wgs84, mercator);
const mercator_bounds = {
    lon: [-20026376.39, 20026376.39],
    lat: [-20048966.10, 20048966.10],
};
const latlon_bounds = {
    lon: [-180, 180],
    lat: [-85.06, 85.06],
};
function clip_mercator(low, high, dimension) {
    const [min, max] = mercator_bounds[dimension];
    return [Math.max(low, min), Math.min(high, max)];
}
exports.clip_mercator = clip_mercator;
function in_bounds(value, dimension) {
    return value > latlon_bounds[dimension][0] && value < latlon_bounds[dimension][1];
}
exports.in_bounds = in_bounds;
function project_xy(x, y) {
    const n = Math.min(x.length, y.length);
    const merc_x_s = new Array(n);
    const merc_y_s = new Array(n);
    for (let i = 0; i < n; i++) {
        const [merc_x, merc_y] = exports.wgs84_mercator.forward([x[i], y[i]]);
        merc_x_s[i] = merc_x;
        merc_y_s[i] = merc_y;
    }
    return [merc_x_s, merc_y_s];
}
exports.project_xy = project_xy;
function project_xsys(xs, ys) {
    const n = Math.min(xs.length, ys.length);
    const merc_xs_s = new Array(n);
    const merc_ys_s = new Array(n);
    for (let i = 0; i < n; i++) {
        const [merc_x_s, merc_y_s] = project_xy(xs[i], ys[i]);
        merc_xs_s[i] = merc_x_s;
        merc_ys_s[i] = merc_y_s;
    }
    return [merc_xs_s, merc_ys_s];
}
exports.project_xsys = project_xsys;
