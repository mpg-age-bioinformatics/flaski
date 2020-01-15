"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const text_input_1 = require("./text_input");
const input_widget_1 = require("./input_widget");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const inputs_1 = require("../../styles/widgets/inputs");
class TextAreaInputView extends input_widget_1.InputWidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.name.change, () => this.input_el.name = this.model.name || "");
        this.connect(this.model.properties.value.change, () => this.input_el.value = this.model.value);
        this.connect(this.model.properties.disabled.change, () => this.input_el.disabled = this.model.disabled);
        this.connect(this.model.properties.placeholder.change, () => this.input_el.placeholder = this.model.placeholder);
        this.connect(this.model.properties.rows.change, () => this.input_el.rows = this.model.rows);
        this.connect(this.model.properties.cols.change, () => this.input_el.cols = this.model.cols);
        this.connect(this.model.properties.max_length.change, () => this.input_el.maxLength = this.model.max_length);
    }
    render() {
        super.render();
        this.input_el = dom_1.textarea({
            class: inputs_1.bk_input,
            name: this.model.name,
            disabled: this.model.disabled,
            placeholder: this.model.placeholder,
            cols: this.model.cols,
            rows: this.model.rows,
            maxLength: this.model.max_length,
        });
        this.input_el.textContent = this.model.value;
        this.input_el.addEventListener("change", () => this.change_input());
        this.group_el.appendChild(this.input_el);
    }
    change_input() {
        this.model.value = this.input_el.value;
        super.change_input();
    }
}
exports.TextAreaInputView = TextAreaInputView;
TextAreaInputView.__name__ = "TextAreaInputView";
class TextAreaInput extends text_input_1.TextInput {
    constructor(attrs) {
        super(attrs);
    }
    static init_TextAreaInput() {
        this.prototype.default_view = TextAreaInputView;
        this.define({
            cols: [p.Number, 20],
            rows: [p.Number, 2],
            max_length: [p.Number, 500],
        });
    }
}
exports.TextAreaInput = TextAreaInput;
TextAreaInput.__name__ = "TextAreaInput";
TextAreaInput.init_TextAreaInput();
