"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const array_1 = require("./util/array");
function build_views(view_storage, models, options, cls = (model) => model.default_view) {
    const to_remove = array_1.difference(Object.keys(view_storage), models.map((model) => model.id));
    for (const model_id of to_remove) {
        view_storage[model_id].remove();
        delete view_storage[model_id];
    }
    const created_views = [];
    const new_models = models.filter((model) => view_storage[model.id] == null);
    for (const model of new_models) {
        const view_cls = cls(model);
        const view_options = Object.assign(Object.assign({}, options), { model, connect_signals: false });
        const view = new view_cls(view_options);
        view_storage[model.id] = view;
        created_views.push(view);
    }
    for (const view of created_views)
        view.connect_signals();
    return created_views;
}
exports.build_views = build_views;
function remove_views(view_storage) {
    for (const id in view_storage) {
        view_storage[id].remove();
        delete view_storage[id];
    }
}
exports.remove_views = remove_views;
