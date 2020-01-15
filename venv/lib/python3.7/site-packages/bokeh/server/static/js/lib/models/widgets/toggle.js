"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const abstract_button_1 = require("./abstract_button");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const mixins_1 = require("../../styles/mixins");
class ToggleView extends abstract_button_1.AbstractButtonView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.active.change, () => this._update_active());
    }
    render() {
        super.render();
        this._update_active();
    }
    click() {
        this.model.active = !this.model.active;
        super.click();
    }
    _update_active() {
        dom_1.classes(this.button_el).toggle(mixins_1.bk_active, this.model.active);
    }
}
exports.ToggleView = ToggleView;
ToggleView.__name__ = "ToggleView";
class Toggle extends abstract_button_1.AbstractButton {
    constructor(attrs) {
        super(attrs);
    }
    static init_Toggle() {
        this.prototype.default_view = ToggleView;
        this.define({
            active: [p.Boolean, false],
        });
        this.override({
            label: "Toggle",
        });
    }
}
exports.Toggle = Toggle;
Toggle.__name__ = "Toggle";
Toggle.init_Toggle();
