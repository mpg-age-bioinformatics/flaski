"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dom_1 = require("../../core/dom");
const string_1 = require("../../core/util/string");
const p = require("../../core/properties");
const input_group_1 = require("./input_group");
const mixins_1 = require("../../styles/mixins");
const inputs_1 = require("../../styles/widgets/inputs");
class RadioGroupView extends input_group_1.InputGroupView {
    render() {
        super.render();
        const group = dom_1.div({ class: [inputs_1.bk_input_group, this.model.inline ? mixins_1.bk_inline : null] });
        this.el.appendChild(group);
        const name = string_1.uniqueId();
        const { active, labels } = this.model;
        for (let i = 0; i < labels.length; i++) {
            const radio = dom_1.input({ type: `radio`, name, value: `${i}` });
            radio.addEventListener("change", () => this.change_active(i));
            if (this.model.disabled)
                radio.disabled = true;
            if (i == active)
                radio.checked = true;
            const label_el = dom_1.label({}, radio, dom_1.span({}, labels[i]));
            group.appendChild(label_el);
        }
    }
    change_active(i) {
        this.model.active = i;
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
}
exports.RadioGroupView = RadioGroupView;
RadioGroupView.__name__ = "RadioGroupView";
class RadioGroup extends input_group_1.InputGroup {
    constructor(attrs) {
        super(attrs);
    }
    static init_RadioGroup() {
        this.prototype.default_view = RadioGroupView;
        this.define({
            active: [p.Number],
            labels: [p.Array, []],
            inline: [p.Boolean, false],
            callback: [p.Any],
        });
    }
}
exports.RadioGroup = RadioGroup;
RadioGroup.__name__ = "RadioGroup";
RadioGroup.init_RadioGroup();
