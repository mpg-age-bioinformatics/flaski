"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dom_view_1 = require("../../core/dom_view");
const visuals = require("../../core/visuals");
const p = require("../../core/properties");
const model_1 = require("../../model");
// This shouldn't be a DOMView, but annotations create a mess.
class RendererView extends dom_view_1.DOMView {
    initialize() {
        super.initialize();
        this.visuals = new visuals.Visuals(this.model);
        this._has_finished = true; // XXX: should be in render() but subclasses don't respect super()
    }
    get plot_view() {
        return this.parent;
    }
    get plot_model() {
        return this.parent.model;
    }
    request_render() {
        this.plot_view.request_render();
    }
    map_to_screen(x, y) {
        return this.plot_view.map_to_screen(x, y, this.model.x_range_name, this.model.y_range_name);
    }
    get needs_clip() {
        return false;
    }
    notify_finished() {
        this.plot_view.notify_finished();
    }
    get has_webgl() {
        return false;
    }
}
exports.RendererView = RendererView;
RendererView.__name__ = "RendererView";
class Renderer extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_Renderer() {
        this.define({
            level: [p.RenderLevel],
            visible: [p.Boolean, true],
        });
    }
}
exports.Renderer = Renderer;
Renderer.__name__ = "Renderer";
Renderer.init_Renderer();
