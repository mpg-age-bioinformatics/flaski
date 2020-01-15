"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const document_1 = require("../document");
const dom_1 = require("../core/dom");
const dom_2 = require("./dom");
// A map from the root model IDs to their views.
exports.index = {};
function _create_view(model) {
    const view = new model.default_view({ model, parent: null });
    exports.index[model.id] = view;
    return view;
}
function add_document_standalone(document, element, roots = {}, use_for_title = false) {
    // this is a LOCAL index of views used only by this particular rendering
    // call, so we can remove the views we create.
    const views = {};
    function render_model(model) {
        let root_el;
        if (model.id in roots)
            root_el = roots[model.id];
        else if (element.classList.contains(dom_2.BOKEH_ROOT))
            root_el = element;
        else {
            root_el = dom_1.div({ class: dom_2.BOKEH_ROOT });
            element.appendChild(root_el);
        }
        const view = _create_view(model);
        view.renderTo(root_el);
        views[model.id] = view;
    }
    function unrender_model(model) {
        const { id } = model;
        if (id in views) {
            const view = views[id];
            view.remove();
            delete views[id];
            delete exports.index[id];
        }
    }
    for (const model of document.roots())
        render_model(model);
    if (use_for_title)
        window.document.title = document.title();
    document.on_change((event) => {
        if (event instanceof document_1.RootAddedEvent)
            render_model(event.model);
        else if (event instanceof document_1.RootRemovedEvent)
            unrender_model(event.model);
        else if (use_for_title && event instanceof document_1.TitleChangedEvent)
            window.document.title = event.title;
    });
    return views;
}
exports.add_document_standalone = add_document_standalone;
