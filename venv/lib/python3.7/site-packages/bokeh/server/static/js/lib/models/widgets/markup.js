"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const layout_1 = require("../../core/layout");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const widget_1 = require("./widget");
const clearfix_1 = require("../../styles/clearfix");
class MarkupView extends widget_1.WidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => {
            this.render();
            this.root.compute_layout(); // XXX: invalidate_layout?
        });
    }
    _update_layout() {
        this.layout = new layout_1.VariadicBox(this.el);
        this.layout.set_sizing(this.box_sizing());
    }
    render() {
        super.render();
        const style = Object.assign(Object.assign({}, this.model.style), { display: "inline-block" });
        this.markup_el = dom_1.div({ class: clearfix_1.bk_clearfix, style });
        this.el.appendChild(this.markup_el);
    }
}
exports.MarkupView = MarkupView;
MarkupView.__name__ = "MarkupView";
class Markup extends widget_1.Widget {
    constructor(attrs) {
        super(attrs);
    }
    static init_Markup() {
        this.define({
            text: [p.String, ''],
            style: [p.Any, {}],
        });
    }
}
exports.Markup = Markup;
Markup.__name__ = "Markup";
Markup.init_Markup();
