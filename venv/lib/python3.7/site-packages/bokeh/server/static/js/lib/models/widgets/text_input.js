"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const input_widget_1 = require("./input_widget");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const inputs_1 = require("../../styles/widgets/inputs");
class TextInputView extends input_widget_1.InputWidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.name.change, () => this.input_el.name = this.model.name || "");
        this.connect(this.model.properties.value.change, () => this.input_el.value = this.model.value);
        this.connect(this.model.properties.value_input.change, () => this.input_el.value = this.model.value_input);
        this.connect(this.model.properties.disabled.change, () => this.input_el.disabled = this.model.disabled);
        this.connect(this.model.properties.placeholder.change, () => this.input_el.placeholder = this.model.placeholder);
    }
    render() {
        super.render();
        this.input_el = dom_1.input({
            type: "text",
            class: inputs_1.bk_input,
            name: this.model.name,
            value: this.model.value,
            disabled: this.model.disabled,
            placeholder: this.model.placeholder,
        });
        this.input_el.addEventListener("change", () => this.change_input());
        this.input_el.addEventListener("input", () => this.change_input_oninput());
        this.group_el.appendChild(this.input_el);
    }
    change_input() {
        this.model.value = this.input_el.value;
        super.change_input();
    }
    change_input_oninput() {
        this.model.value_input = this.input_el.value;
        super.change_input();
    }
}
exports.TextInputView = TextInputView;
TextInputView.__name__ = "TextInputView";
class TextInput extends input_widget_1.InputWidget {
    constructor(attrs) {
        super(attrs);
    }
    static init_TextInput() {
        this.prototype.default_view = TextInputView;
        this.define({
            value: [p.String, ""],
            value_input: [p.String, ""],
            placeholder: [p.String, ""],
        });
    }
}
exports.TextInput = TextInput;
TextInput.__name__ = "TextInput";
TextInput.init_TextInput();
