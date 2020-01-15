"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
class SelectionPolicy extends model_1.Model {
    do_selection(hit_test_result, source, final, append) {
        if (hit_test_result === null) {
            return false;
        }
        else {
            source.selected.update(hit_test_result, final, append);
            source._select.emit();
            return !source.selected.is_empty();
        }
    }
}
exports.SelectionPolicy = SelectionPolicy;
SelectionPolicy.__name__ = "SelectionPolicy";
class IntersectRenderers extends SelectionPolicy {
    hit_test(geometry, renderer_views) {
        const hit_test_result_renderers = [];
        for (const r of renderer_views) {
            const result = r.hit_test(geometry);
            if (result !== null)
                hit_test_result_renderers.push(result);
        }
        if (hit_test_result_renderers.length > 0) {
            const hit_test_result = hit_test_result_renderers[0];
            for (const hit_test_result_other of hit_test_result_renderers) {
                hit_test_result.update_through_intersection(hit_test_result_other);
            }
            return hit_test_result;
        }
        else {
            return null;
        }
    }
}
exports.IntersectRenderers = IntersectRenderers;
IntersectRenderers.__name__ = "IntersectRenderers";
class UnionRenderers extends SelectionPolicy {
    hit_test(geometry, renderer_views) {
        const hit_test_result_renderers = [];
        for (const r of renderer_views) {
            const result = r.hit_test(geometry);
            if (result !== null)
                hit_test_result_renderers.push(result);
        }
        if (hit_test_result_renderers.length > 0) {
            const hit_test_result = hit_test_result_renderers[0];
            for (const hit_test_result_other of hit_test_result_renderers) {
                hit_test_result.update_through_union(hit_test_result_other);
            }
            return hit_test_result;
        }
        else {
            return null;
        }
    }
}
exports.UnionRenderers = UnionRenderers;
UnionRenderers.__name__ = "UnionRenderers";
