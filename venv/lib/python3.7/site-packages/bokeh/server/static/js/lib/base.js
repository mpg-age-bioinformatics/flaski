"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const types_1 = require("./core/util/types");
const has_props_1 = require("./core/has_props");
exports.overrides = {};
const _all_models = new Map();
exports.Models = ((name) => {
    const model = exports.overrides[name] || _all_models.get(name);
    if (model == null) {
        throw new Error(`Model '${name}' does not exist. This could be due to a widget or a custom model not being registered before first usage.`);
    }
    return model;
});
exports.Models.register = (name, model) => {
    exports.overrides[name] = model;
};
exports.Models.unregister = (name) => {
    delete exports.overrides[name];
};
function is_HasProps(obj) {
    return types_1.isObject(obj) && obj.prototype instanceof has_props_1.HasProps;
}
exports.Models.register_models = (models, force = false, errorFn) => {
    if (models == null)
        return;
    for (const name in models) {
        const model = models[name];
        if (is_HasProps(model)) {
            const qualified = model.__qualified__;
            if (force || !_all_models.has(qualified))
                _all_models.set(qualified, model);
            else if (errorFn != null)
                errorFn(qualified);
            else
                console.warn(`Model '${qualified}' was already registered`);
        }
    }
};
exports.register_models = exports.Models.register_models;
exports.Models.registered_names = () => Array.from(_all_models.keys());
// TODO: this doesn't belong here, but it's easier this way for backwards compatibility
const AllModels = require("./models");
exports.register_models(AllModels);
