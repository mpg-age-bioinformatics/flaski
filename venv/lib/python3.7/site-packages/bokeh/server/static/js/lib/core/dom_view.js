"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const view_1 = require("./view");
const DOM = require("./dom");
const root_1 = require("../styles/root");
class DOMView extends view_1.View {
    initialize() {
        super.initialize();
        this._has_finished = false;
        this.el = this._createElement();
    }
    remove() {
        DOM.removeElement(this.el);
        super.remove();
    }
    css_classes() {
        return [];
    }
    cursor(_sx, _sy) {
        return null;
    }
    render() { }
    renderTo(element) {
        element.appendChild(this.el);
        this.render();
    }
    has_finished() {
        return this._has_finished;
    }
    get _root_element() {
        return DOM.parent(this.el, `.${root_1.bk_root}`) || document.body;
    }
    get is_idle() {
        return this.has_finished();
    }
    _createElement() {
        return DOM.createElement(this.tagName, { class: this.css_classes() });
    }
}
exports.DOMView = DOMView;
DOMView.__name__ = "DOMView";
DOMView.prototype.tagName = "div";
