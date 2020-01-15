"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const abstract_button_1 = require("./abstract_button");
const bokeh_events_1 = require("../../core/bokeh_events");
const p = require("../../core/properties");
class ButtonView extends abstract_button_1.AbstractButtonView {
    click() {
        this.model.clicks = this.model.clicks + 1;
        this.model.trigger_event(new bokeh_events_1.ButtonClick());
        super.click();
    }
}
exports.ButtonView = ButtonView;
ButtonView.__name__ = "ButtonView";
class Button extends abstract_button_1.AbstractButton {
    constructor(attrs) {
        super(attrs);
    }
    static init_Button() {
        this.prototype.default_view = ButtonView;
        this.define({
            clicks: [p.Number, 0],
        });
        this.override({
            label: "Button",
        });
    }
}
exports.Button = Button;
Button.__name__ = "Button";
Button.init_Button();
