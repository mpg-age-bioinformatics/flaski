"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const control_1 = require("./control");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const buttons_1 = require("../../styles/buttons");
class ButtonGroupView extends control_1.ControlView {
    connect_signals() {
        super.connect_signals();
        const p = this.model.properties;
        this.on_change(p.button_type, () => this.render());
        this.on_change(p.labels, () => this.render());
        this.on_change(p.active, () => this._update_active());
    }
    render() {
        super.render();
        this._buttons = this.model.labels.map((label, i) => {
            const button = dom_1.div({
                class: [buttons_1.bk_btn, buttons_1.bk_btn_type(this.model.button_type)],
                disabled: this.model.disabled,
            }, label);
            button.addEventListener("click", () => this.change_active(i));
            return button;
        });
        this._update_active();
        const group = dom_1.div({ class: buttons_1.bk_btn_group }, this._buttons);
        this.el.appendChild(group);
    }
}
exports.ButtonGroupView = ButtonGroupView;
ButtonGroupView.__name__ = "ButtonGroupView";
class ButtonGroup extends control_1.Control {
    constructor(attrs) {
        super(attrs);
    }
    static init_ButtonGroup() {
        this.define({
            labels: [p.Array, []],
            button_type: [p.ButtonType, "default"],
            callback: [p.Any],
        });
    }
}
exports.ButtonGroup = ButtonGroup;
ButtonGroup.__name__ = "ButtonGroup";
ButtonGroup.init_ButtonGroup();
