"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const annotation_1 = require("./annotation");
const build_views_1 = require("../../core/build_views");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
class ToolbarPanelView extends annotation_1.AnnotationView {
    constructor() {
        super(...arguments);
        this.rotate = true;
    }
    initialize() {
        super.initialize();
        this.plot_view.canvas_events.appendChild(this.el);
        this._toolbar_views = {};
        build_views_1.build_views(this._toolbar_views, [this.model.toolbar], { parent: this });
        const toolbar_view = this._toolbar_views[this.model.toolbar.id];
        this.plot_view.visibility_callbacks.push((visible) => toolbar_view.set_visibility(visible));
    }
    remove() {
        build_views_1.remove_views(this._toolbar_views);
        super.remove();
    }
    render() {
        super.render();
        if (!this.model.visible) {
            dom_1.undisplay(this.el);
            return;
        }
        this.el.style.position = "absolute";
        this.el.style.overflow = "hidden";
        dom_1.position(this.el, this.panel.bbox);
        const toolbar_view = this._toolbar_views[this.model.toolbar.id];
        toolbar_view.render();
        dom_1.empty(this.el);
        this.el.appendChild(toolbar_view.el);
        dom_1.display(this.el);
    }
    _get_size() {
        const { tools, logo } = this.model.toolbar;
        return {
            width: tools.length * 30 + (logo != null ? 25 : 0),
            height: 30,
        };
    }
}
exports.ToolbarPanelView = ToolbarPanelView;
ToolbarPanelView.__name__ = "ToolbarPanelView";
class ToolbarPanel extends annotation_1.Annotation {
    constructor(attrs) {
        super(attrs);
    }
    static init_ToolbarPanel() {
        this.prototype.default_view = ToolbarPanelView;
        this.define({
            toolbar: [p.Instance],
        });
    }
}
exports.ToolbarPanel = ToolbarPanel;
ToolbarPanel.__name__ = "ToolbarPanel";
ToolbarPanel.init_ToolbarPanel();
