"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const markup_1 = require("./markup");
const p = require("../../core/properties");
class DivView extends markup_1.MarkupView {
    render() {
        super.render();
        if (this.model.render_as_text)
            this.markup_el.textContent = this.model.text;
        else
            this.markup_el.innerHTML = this.model.text;
    }
}
exports.DivView = DivView;
DivView.__name__ = "DivView";
class Div extends markup_1.Markup {
    constructor(attrs) {
        super(attrs);
    }
    static init_Div() {
        this.prototype.default_view = DivView;
        this.define({
            render_as_text: [p.Boolean, false],
        });
    }
}
exports.Div = Div;
Div.__name__ = "Div";
Div.init_Div();
