"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const dom_1 = require("../../core/dom");
const build_views_1 = require("../../core/build_views");
const control_1 = require("./control");
const buttons_1 = require("../../styles/buttons");
class AbstractButtonView extends control_1.ControlView {
    initialize() {
        super.initialize();
        this.icon_views = {};
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.render());
    }
    remove() {
        build_views_1.remove_views(this.icon_views);
        super.remove();
    }
    _render_button(...children) {
        return dom_1.button({
            type: "button",
            disabled: this.model.disabled,
            class: [buttons_1.bk_btn, buttons_1.bk_btn_type(this.model.button_type)],
        }, ...children);
    }
    render() {
        super.render();
        this.button_el = this._render_button(this.model.label);
        this.button_el.addEventListener("click", () => this.click());
        const icon = this.model.icon;
        if (icon != null) {
            build_views_1.build_views(this.icon_views, [icon], { parent: this });
            const icon_view = this.icon_views[icon.id];
            icon_view.render();
            dom_1.prepend(this.button_el, icon_view.el, dom_1.nbsp());
        }
        this.group_el = dom_1.div({ class: buttons_1.bk_btn_group }, this.button_el);
        this.el.appendChild(this.group_el);
    }
    click() {
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
}
exports.AbstractButtonView = AbstractButtonView;
AbstractButtonView.__name__ = "AbstractButtonView";
class AbstractButton extends control_1.Control {
    constructor(attrs) {
        super(attrs);
    }
    static init_AbstractButton() {
        this.define({
            label: [p.String, "Button"],
            icon: [p.Instance],
            button_type: [p.ButtonType, "default"],
            callback: [p.Any],
        });
    }
}
exports.AbstractButton = AbstractButton;
AbstractButton.__name__ = "AbstractButton";
AbstractButton.init_AbstractButton();
