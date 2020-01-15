"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const projections_1 = require("../../core/util/projections");
function geographic_to_meters(xLon, yLat) {
    return projections_1.wgs84_mercator.forward([xLon, yLat]);
}
exports.geographic_to_meters = geographic_to_meters;
function meters_to_geographic(mx, my) {
    return projections_1.wgs84_mercator.inverse([mx, my]);
}
exports.meters_to_geographic = meters_to_geographic;
function geographic_extent_to_meters(extent) {
    const [g_xmin, g_ymin, g_xmax, g_ymax] = extent;
    const [m_xmin, m_ymin] = geographic_to_meters(g_xmin, g_ymin);
    const [m_xmax, m_ymax] = geographic_to_meters(g_xmax, g_ymax);
    return [m_xmin, m_ymin, m_xmax, m_ymax];
}
exports.geographic_extent_to_meters = geographic_extent_to_meters;
function meters_extent_to_geographic(extent) {
    const [m_xmin, m_ymin, m_xmax, m_ymax] = extent;
    const [g_xmin, g_ymin] = meters_to_geographic(m_xmin, m_ymin);
    const [g_xmax, g_ymax] = meters_to_geographic(m_xmax, m_ymax);
    return [g_xmin, g_ymin, g_xmax, g_ymax];
}
exports.meters_extent_to_geographic = meters_extent_to_geographic;
