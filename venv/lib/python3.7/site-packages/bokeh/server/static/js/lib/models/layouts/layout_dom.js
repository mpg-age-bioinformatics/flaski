"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const dom_1 = require("../../core/dom");
const logging_1 = require("../../core/logging");
const types_1 = require("../../core/util/types");
const p = require("../../core/properties");
const build_views_1 = require("../../core/build_views");
const dom_view_1 = require("../../core/dom_view");
const root_1 = require("../../styles/root");
class LayoutDOMView extends dom_view_1.DOMView {
    constructor() {
        super(...arguments);
        this._idle_notified = false;
        this._offset_parent = null;
        this._viewport = {};
    }
    initialize() {
        super.initialize();
        this.el.style.position = this.is_root ? "relative" : "absolute";
        this._child_views = {};
        this.build_child_views();
    }
    remove() {
        for (const child_view of this.child_views)
            child_view.remove();
        this._child_views = {};
        super.remove();
    }
    connect_signals() {
        super.connect_signals();
        if (this.is_root) {
            this._on_resize = () => this.resize_layout();
            window.addEventListener("resize", this._on_resize);
            this._parent_observer = setInterval(() => {
                const offset_parent = this.el.offsetParent;
                if (this._offset_parent != offset_parent) {
                    this._offset_parent = offset_parent;
                    if (offset_parent != null) {
                        this.compute_viewport();
                        this.invalidate_layout();
                    }
                }
            }, 250);
        }
        const p = this.model.properties;
        this.on_change([
            p.width, p.height,
            p.min_width, p.min_height,
            p.max_width, p.max_height,
            p.margin,
            p.width_policy, p.height_policy, p.sizing_mode,
            p.aspect_ratio,
            p.visible,
        ], () => this.invalidate_layout());
        this.on_change([
            p.background,
            p.css_classes,
        ], () => this.invalidate_render());
    }
    disconnect_signals() {
        if (this._parent_observer != null)
            clearTimeout(this._parent_observer);
        if (this._on_resize != null)
            window.removeEventListener("resize", this._on_resize);
        super.disconnect_signals();
    }
    css_classes() {
        return super.css_classes().concat(this.model.css_classes);
    }
    get child_views() {
        return this.child_models.map((child) => this._child_views[child.id]);
    }
    build_child_views() {
        build_views_1.build_views(this._child_views, this.child_models, { parent: this });
    }
    render() {
        super.render();
        dom_1.empty(this.el); // XXX: this should be in super
        const { background } = this.model;
        this.el.style.backgroundColor = background != null ? background : "";
        dom_1.classes(this.el).clear().add(...this.css_classes());
        for (const child_view of this.child_views) {
            this.el.appendChild(child_view.el);
            child_view.render();
        }
    }
    update_layout() {
        for (const child_view of this.child_views)
            child_view.update_layout();
        this._update_layout();
    }
    update_position() {
        this.el.style.display = this.model.visible ? "block" : "none";
        const margin = this.is_root ? this.layout.sizing.margin : undefined;
        dom_1.position(this.el, this.layout.bbox, margin);
        for (const child_view of this.child_views)
            child_view.update_position();
    }
    after_layout() {
        for (const child_view of this.child_views)
            child_view.after_layout();
        this._has_finished = true;
    }
    compute_viewport() {
        this._viewport = this._viewport_size();
    }
    renderTo(element) {
        element.appendChild(this.el);
        this._offset_parent = this.el.offsetParent;
        this.compute_viewport();
        this.build();
    }
    build() {
        this.assert_root();
        this.render();
        this.update_layout();
        this.compute_layout();
        return this;
    }
    rebuild() {
        this.build_child_views();
        this.invalidate_render();
    }
    compute_layout() {
        const start = Date.now();
        this.layout.compute(this._viewport);
        this.update_position();
        this.after_layout();
        logging_1.logger.debug(`layout computed in ${Date.now() - start} ms`);
        this.notify_finished();
    }
    resize_layout() {
        this.root.compute_viewport();
        this.root.compute_layout();
    }
    invalidate_layout() {
        this.root.update_layout();
        this.root.compute_layout();
    }
    invalidate_render() {
        this.render();
        this.invalidate_layout();
    }
    has_finished() {
        if (!super.has_finished())
            return false;
        for (const child_view of this.child_views) {
            if (!child_view.has_finished())
                return false;
        }
        return true;
    }
    notify_finished() {
        if (!this.is_root)
            this.root.notify_finished();
        else {
            if (!this._idle_notified && this.has_finished()) {
                if (this.model.document != null) {
                    this._idle_notified = true;
                    this.model.document.notify_idle(this.model);
                }
            }
        }
    }
    _width_policy() {
        return this.model.width != null ? "fixed" : "fit";
    }
    _height_policy() {
        return this.model.height != null ? "fixed" : "fit";
    }
    box_sizing() {
        let { width_policy, height_policy, aspect_ratio } = this.model;
        if (width_policy == "auto")
            width_policy = this._width_policy();
        if (height_policy == "auto")
            height_policy = this._height_policy();
        const { sizing_mode } = this.model;
        if (sizing_mode != null) {
            if (sizing_mode == "fixed")
                width_policy = height_policy = "fixed";
            else if (sizing_mode == "stretch_both")
                width_policy = height_policy = "max";
            else if (sizing_mode == "stretch_width")
                width_policy = "max";
            else if (sizing_mode == "stretch_height")
                height_policy = "max";
            else {
                if (aspect_ratio == null)
                    aspect_ratio = "auto";
                switch (sizing_mode) {
                    case "scale_width":
                        width_policy = "max";
                        height_policy = "min";
                        break;
                    case "scale_height":
                        width_policy = "min";
                        height_policy = "max";
                        break;
                    case "scale_both":
                        width_policy = "max";
                        height_policy = "max";
                        break;
                    default:
                        throw new Error("unreachable");
                }
            }
        }
        const sizing = { width_policy, height_policy };
        const { min_width, min_height } = this.model;
        if (min_width != null)
            sizing.min_width = min_width;
        if (min_height != null)
            sizing.min_height = min_height;
        const { width, height } = this.model;
        if (width != null)
            sizing.width = width;
        if (height != null)
            sizing.height = height;
        const { max_width, max_height } = this.model;
        if (max_width != null)
            sizing.max_width = max_width;
        if (max_height != null)
            sizing.max_height = max_height;
        if (aspect_ratio == "auto" && width != null && height != null)
            sizing.aspect = width / height;
        else if (types_1.isNumber(aspect_ratio))
            sizing.aspect = aspect_ratio;
        const { margin } = this.model;
        if (margin != null) {
            if (types_1.isNumber(margin))
                sizing.margin = { top: margin, right: margin, bottom: margin, left: margin };
            else if (margin.length == 2) {
                const [vertical, horizontal] = margin;
                sizing.margin = { top: vertical, right: horizontal, bottom: vertical, left: horizontal };
            }
            else {
                const [top, right, bottom, left] = margin;
                sizing.margin = { top, right, bottom, left };
            }
        }
        sizing.visible = this.model.visible;
        const { align } = this.model;
        if (types_1.isArray(align))
            [sizing.halign, sizing.valign] = align;
        else
            sizing.halign = sizing.valign = align;
        return sizing;
    }
    _viewport_size() {
        return dom_1.undisplayed(this.el, () => {
            let measuring = this.el;
            while (measuring = measuring.parentElement) {
                // .bk-root element doesn't bring any value
                if (measuring.classList.contains(root_1.bk_root))
                    continue;
                // we reached <body> element, so use viewport size
                if (measuring == document.body) {
                    const { margin: { left, right, top, bottom } } = dom_1.extents(document.body);
                    const width = Math.ceil(document.documentElement.clientWidth - left - right);
                    const height = Math.ceil(document.documentElement.clientHeight - top - bottom);
                    return { width, height };
                }
                // stop on first element with sensible dimensions
                const { padding: { left, right, top, bottom } } = dom_1.extents(measuring);
                const { width, height } = measuring.getBoundingClientRect();
                const inner_width = Math.ceil(width - left - right);
                const inner_height = Math.ceil(height - top - bottom);
                if (inner_width > 0 || inner_height > 0)
                    return {
                        width: inner_width > 0 ? inner_width : undefined,
                        height: inner_height > 0 ? inner_height : undefined,
                    };
            }
            // this element is detached from DOM
            return {};
        });
    }
    serializable_state() {
        return Object.assign(Object.assign({}, super.serializable_state()), { bbox: this.layout.bbox.box, children: this.child_views.map((child) => child.serializable_state()) });
    }
}
exports.LayoutDOMView = LayoutDOMView;
LayoutDOMView.__name__ = "LayoutDOMView";
class LayoutDOM extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_LayoutDOM() {
        this.define({
            width: [p.Number, null],
            height: [p.Number, null],
            min_width: [p.Number, null],
            min_height: [p.Number, null],
            max_width: [p.Number, null],
            max_height: [p.Number, null],
            margin: [p.Any, [0, 0, 0, 0]],
            width_policy: [p.Any, "auto"],
            height_policy: [p.Any, "auto"],
            aspect_ratio: [p.Any, null],
            sizing_mode: [p.SizingMode, null],
            visible: [p.Boolean, true],
            disabled: [p.Boolean, false],
            align: [p.Any, "start"],
            background: [p.Color, null],
            css_classes: [p.Array, []],
        });
    }
}
exports.LayoutDOM = LayoutDOM;
LayoutDOM.__name__ = "LayoutDOM";
LayoutDOM.init_LayoutDOM();
