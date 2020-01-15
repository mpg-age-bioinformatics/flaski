"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const proj = require("../../core/util/projections");
const object_1 = require("../../core/util/object");
const renderer_1 = require("../renderers/renderer");
class AnnotationView extends renderer_1.RendererView {
    get panel() {
        return this.layout;
    }
    get_size() {
        if (this.model.visible) {
            const { width, height } = this._get_size();
            return { width: Math.round(width), height: Math.round(height) };
        }
        else
            return { width: 0, height: 0 };
    }
    connect_signals() {
        super.connect_signals();
        const p = this.model.properties;
        this.on_change(p.visible, () => this.plot_view.request_layout());
    }
    _get_size() {
        throw new Error("not implemented");
    }
    get ctx() {
        return this.plot_view.canvas_view.ctx;
    }
    set_data(source) {
        const data = this.model.materialize_dataspecs(source);
        object_1.extend(this, data);
        if (this.plot_model.use_map) {
            const self = this;
            if (self._x != null)
                [self._x, self._y] = proj.project_xy(self._x, self._y);
            if (self._xs != null)
                [self._xs, self._ys] = proj.project_xsys(self._xs, self._ys);
        }
    }
    get needs_clip() {
        return this.layout == null; // TODO: change this, when center layout is fully implemented
    }
    serializable_state() {
        const state = super.serializable_state();
        return this.layout == null ? state : Object.assign(Object.assign({}, state), { bbox: this.layout.bbox.box });
    }
}
exports.AnnotationView = AnnotationView;
AnnotationView.__name__ = "AnnotationView";
class Annotation extends renderer_1.Renderer {
    constructor(attrs) {
        super(attrs);
    }
    static init_Annotation() {
        this.override({
            level: 'annotation',
        });
    }
}
exports.Annotation = Annotation;
Annotation.__name__ = "Annotation";
Annotation.init_Annotation();
