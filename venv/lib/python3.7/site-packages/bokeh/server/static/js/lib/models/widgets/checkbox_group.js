"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const input_group_1 = require("./input_group");
const dom_1 = require("../../core/dom");
const array_1 = require("../../core/util/array");
const data_structures_1 = require("../../core/util/data_structures");
const p = require("../../core/properties");
const mixins_1 = require("../../styles/mixins");
const inputs_1 = require("../../styles/widgets/inputs");
class CheckboxGroupView extends input_group_1.InputGroupView {
    render() {
        super.render();
        const group = dom_1.div({ class: [inputs_1.bk_input_group, this.model.inline ? mixins_1.bk_inline : null] });
        this.el.appendChild(group);
        const { active, labels } = this.model;
        for (let i = 0; i < labels.length; i++) {
            const checkbox = dom_1.input({ type: `checkbox`, value: `${i}` });
            checkbox.addEventListener("change", () => this.change_active(i));
            if (this.model.disabled)
                checkbox.disabled = true;
            if (array_1.includes(active, i))
                checkbox.checked = true;
            const label_el = dom_1.label({}, checkbox, dom_1.span({}, labels[i]));
            group.appendChild(label_el);
        }
    }
    change_active(i) {
        const active = new data_structures_1.Set(this.model.active);
        active.toggle(i);
        this.model.active = active.values;
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
}
exports.CheckboxGroupView = CheckboxGroupView;
CheckboxGroupView.__name__ = "CheckboxGroupView";
class CheckboxGroup extends input_group_1.InputGroup {
    constructor(attrs) {
        super(attrs);
    }
    static init_CheckboxGroup() {
        this.prototype.default_view = CheckboxGroupView;
        this.define({
            active: [p.Array, []],
            labels: [p.Array, []],
            inline: [p.Boolean, false],
            callback: [p.Any],
        });
    }
}
exports.CheckboxGroup = CheckboxGroup;
CheckboxGroup.__name__ = "CheckboxGroup";
CheckboxGroup.init_CheckboxGroup();
