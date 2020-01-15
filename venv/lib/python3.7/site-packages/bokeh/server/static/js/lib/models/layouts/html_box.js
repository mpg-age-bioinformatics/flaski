"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_dom_1 = require("../layouts/layout_dom");
const layout_1 = require("../../core/layout");
class HTMLBoxView extends layout_dom_1.LayoutDOMView {
    get child_models() {
        return [];
    }
    _update_layout() {
        this.layout = new layout_1.ContentBox(this.el);
        this.layout.set_sizing(this.box_sizing());
    }
}
exports.HTMLBoxView = HTMLBoxView;
HTMLBoxView.__name__ = "HTMLBoxView";
class HTMLBox extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
}
exports.HTMLBox = HTMLBox;
HTMLBox.__name__ = "HTMLBox";
