"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const markup_1 = require("./markup");
const dom_1 = require("../../core/dom");
class PreTextView extends markup_1.MarkupView {
    render() {
        super.render();
        const content = dom_1.pre({ style: { overflow: "auto" } }, this.model.text);
        this.markup_el.appendChild(content);
    }
}
exports.PreTextView = PreTextView;
PreTextView.__name__ = "PreTextView";
class PreText extends markup_1.Markup {
    constructor(attrs) {
        super(attrs);
    }
    static init_PreText() {
        this.prototype.default_view = PreTextView;
    }
}
exports.PreText = PreText;
PreText.__name__ = "PreText";
PreText.init_PreText();
