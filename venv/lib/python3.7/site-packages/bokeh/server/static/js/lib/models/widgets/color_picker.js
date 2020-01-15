"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const input_widget_1 = require("./input_widget");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const inputs_1 = require("../../styles/widgets/inputs");
class ColorPickerView extends input_widget_1.InputWidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.name.change, () => this.input_el.name = this.model.name || "");
        this.connect(this.model.properties.color.change, () => this.input_el.value = this.model.color);
        this.connect(this.model.properties.disabled.change, () => this.input_el.disabled = this.model.disabled);
    }
    render() {
        super.render();
        this.input_el = dom_1.input({
            type: "color",
            class: inputs_1.bk_input,
            name: this.model.name,
            value: this.model.color,
            disabled: this.model.disabled,
        });
        this.input_el.addEventListener("change", () => this.change_input());
        this.group_el.appendChild(this.input_el);
    }
    change_input() {
        this.model.color = this.input_el.value;
        super.change_input();
    }
}
exports.ColorPickerView = ColorPickerView;
ColorPickerView.__name__ = "ColorPickerView";
class ColorPicker extends input_widget_1.InputWidget {
    constructor(attrs) {
        super(attrs);
    }
    static init_ColorPicker() {
        this.prototype.default_view = ColorPickerView;
        this.define({
            color: [p.Color, "#000000"],
        });
    }
}
exports.ColorPicker = ColorPicker;
ColorPicker.__name__ = "ColorPicker";
ColorPicker.init_ColorPicker();
