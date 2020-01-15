"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const array_1 = require("../../core/util/array");
function compute_renderers(renderers, all_renderers, names) {
    if (renderers == null)
        return [];
    let result = renderers == 'auto' ? all_renderers : renderers;
    if (names.length > 0)
        result = result.filter((r) => array_1.includes(names, r.name));
    return result;
}
exports.compute_renderers = compute_renderers;
