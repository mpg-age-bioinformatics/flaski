"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_dom_1 = require("./layout_dom");
const layout_1 = require("../../core/layout");
class SpacerView extends layout_dom_1.LayoutDOMView {
    get child_models() {
        return [];
    }
    _update_layout() {
        this.layout = new layout_1.LayoutItem();
        this.layout.set_sizing(this.box_sizing());
    }
}
exports.SpacerView = SpacerView;
SpacerView.__name__ = "SpacerView";
class Spacer extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_Spacer() {
        this.prototype.default_view = SpacerView;
    }
}
exports.Spacer = Spacer;
Spacer.__name__ = "Spacer";
Spacer.init_Spacer();
