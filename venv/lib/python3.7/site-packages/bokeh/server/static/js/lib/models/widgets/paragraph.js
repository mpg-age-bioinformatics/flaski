"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const markup_1 = require("./markup");
const dom_1 = require("../../core/dom");
class ParagraphView extends markup_1.MarkupView {
    render() {
        super.render();
        // This overrides default user-agent styling and helps layout work
        const content = dom_1.p({ style: { margin: 0 } }, this.model.text);
        this.markup_el.appendChild(content);
    }
}
exports.ParagraphView = ParagraphView;
ParagraphView.__name__ = "ParagraphView";
class Paragraph extends markup_1.Markup {
    constructor(attrs) {
        super(attrs);
    }
    static init_Paragraph() {
        this.prototype.default_view = ParagraphView;
    }
}
exports.Paragraph = Paragraph;
Paragraph.__name__ = "Paragraph";
Paragraph.init_Paragraph();
