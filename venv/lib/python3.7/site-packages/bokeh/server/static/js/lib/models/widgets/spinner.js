"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const input_widget_1 = require("./input_widget");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const inputs_1 = require("../../styles/widgets/inputs");
const { floor, max, min } = Math;
function _get_sig_dig(num) {
    if (floor(num) !== num)
        return num.toString().replace('/0+$/', '').split(".")[1].length;
    return 0;
}
class SpinnerView extends input_widget_1.InputWidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.low.change, () => {
            const { low } = this.model;
            if (low != null)
                this.input_el.min = low.toFixed(16);
        });
        this.connect(this.model.properties.high.change, () => {
            const { high } = this.model;
            if (high != null)
                this.input_el.max = high.toFixed(16);
        });
        this.connect(this.model.properties.step.change, () => {
            const { step } = this.model;
            this.input_el.step = step.toFixed(16);
        });
        this.connect(this.model.properties.value.change, () => {
            const { value, step } = this.model;
            this.input_el.value = value.toFixed(_get_sig_dig(step)).replace(/(\.[0-9]*[1-9])0+$|\.0*$/, '$1'); //trim last 0
        });
        this.connect(this.model.properties.disabled.change, () => {
            this.input_el.disabled = this.model.disabled;
        });
    }
    render() {
        super.render();
        this.input_el = dom_1.input({
            type: "number",
            class: inputs_1.bk_input,
            name: this.model.name,
            min: this.model.low,
            max: this.model.high,
            value: this.model.value,
            step: this.model.step,
            disabled: this.model.disabled,
        });
        this.input_el.addEventListener("change", () => this.change_input());
        //this.input_el.addEventListener("input", () => this.change_input())
        this.group_el.appendChild(this.input_el);
    }
    change_input() {
        if (this.input_el.value) { //if input is empty skip update
            const { step } = this.model;
            let new_value = Number(this.input_el.value);
            if (this.model.low != null)
                new_value = max(new_value, this.model.low);
            if (this.model.high != null)
                new_value = min(new_value, this.model.high);
            this.model.value = Number(new_value.toFixed(_get_sig_dig(step)));
            super.change_input();
        }
    }
}
exports.SpinnerView = SpinnerView;
SpinnerView.__name__ = "SpinnerView";
class Spinner extends input_widget_1.InputWidget {
    constructor(attrs) {
        super(attrs);
    }
    static init_Spinner() {
        this.prototype.default_view = SpinnerView;
        this.define({
            value: [p.Number, 0],
            low: [p.Number, null],
            high: [p.Number, null],
            step: [p.Number, 1],
        });
    }
}
exports.Spinner = Spinner;
Spinner.__name__ = "Spinner";
Spinner.init_Spinner();
