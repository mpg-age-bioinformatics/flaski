"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dom_1 = require("../../core/dom");
const types_1 = require("../../core/util/types");
const logging_1 = require("../../core/logging");
const p = require("../../core/properties");
const input_widget_1 = require("./input_widget");
const inputs_1 = require("../../styles/widgets/inputs");
class SelectView extends input_widget_1.InputWidgetView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.change, () => this.render());
    }
    build_options(values) {
        return values.map((el) => {
            let value, _label;
            if (types_1.isString(el))
                value = _label = el;
            else
                [value, _label] = el;
            const selected = this.model.value == value;
            return dom_1.option({ selected, value }, _label);
        });
    }
    render() {
        super.render();
        let contents;
        if (types_1.isArray(this.model.options))
            contents = this.build_options(this.model.options);
        else {
            contents = [];
            const options = this.model.options;
            for (const key in options) {
                const value = options[key];
                contents.push(dom_1.optgroup({ label: key }, this.build_options(value)));
            }
        }
        this.select_el = dom_1.select({
            class: inputs_1.bk_input,
            id: this.model.id,
            name: this.model.name,
            disabled: this.model.disabled
        }, contents);
        this.select_el.addEventListener("change", () => this.change_input());
        this.group_el.appendChild(this.select_el);
    }
    change_input() {
        const value = this.select_el.value;
        logging_1.logger.debug(`selectbox: value = ${value}`);
        this.model.value = value;
        super.change_input();
    }
}
exports.SelectView = SelectView;
SelectView.__name__ = "SelectView";
class Select extends input_widget_1.InputWidget {
    constructor(attrs) {
        super(attrs);
    }
    static init_Select() {
        this.prototype.default_view = SelectView;
        this.define({
            value: [p.String, ''],
            options: [p.Any, []],
        });
    }
}
exports.Select = Select;
Select.__name__ = "Select";
Select.init_Select();
