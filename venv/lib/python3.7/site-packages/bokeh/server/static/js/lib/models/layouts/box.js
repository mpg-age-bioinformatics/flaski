"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_dom_1 = require("./layout_dom");
const p = require("../../core/properties");
class BoxView extends layout_dom_1.LayoutDOMView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.children.change, () => this.rebuild());
    }
    get child_models() {
        return this.model.children;
    }
}
exports.BoxView = BoxView;
BoxView.__name__ = "BoxView";
class Box extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_Box() {
        this.define({
            children: [p.Array, []],
            spacing: [p.Number, 0],
        });
    }
}
exports.Box = Box;
Box.__name__ = "Box";
Box.init_Box();
