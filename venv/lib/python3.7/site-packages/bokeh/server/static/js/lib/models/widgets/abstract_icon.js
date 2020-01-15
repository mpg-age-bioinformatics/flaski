"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const model_1 = require("../../model");
const dom_view_1 = require("../../core/dom_view");
class AbstractIconView extends dom_view_1.DOMView {
}
exports.AbstractIconView = AbstractIconView;
AbstractIconView.__name__ = "AbstractIconView";
class AbstractIcon extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
}
exports.AbstractIcon = AbstractIcon;
AbstractIcon.__name__ = "AbstractIcon";
