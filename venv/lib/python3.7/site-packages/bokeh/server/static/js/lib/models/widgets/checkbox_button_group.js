"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_group_1 = require("./button_group");
const dom_1 = require("../../core/dom");
const data_structures_1 = require("../../core/util/data_structures");
const p = require("../../core/properties");
const mixins_1 = require("../../styles/mixins");
class CheckboxButtonGroupView extends button_group_1.ButtonGroupView {
    get active() {
        return new data_structures_1.Set(this.model.active);
    }
    change_active(i) {
        const { active } = this;
        active.toggle(i);
        this.model.active = active.values;
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
    _update_active() {
        const { active } = this;
        this._buttons.forEach((button, i) => {
            dom_1.classes(button).toggle(mixins_1.bk_active, active.has(i));
        });
    }
}
exports.CheckboxButtonGroupView = CheckboxButtonGroupView;
CheckboxButtonGroupView.__name__ = "CheckboxButtonGroupView";
class CheckboxButtonGroup extends button_group_1.ButtonGroup {
    constructor(attrs) {
        super(attrs);
    }
    static init_CheckboxButtonGroup() {
        this.prototype.default_view = CheckboxButtonGroupView;
        this.define({
            active: [p.Array, []],
        });
    }
}
exports.CheckboxButtonGroup = CheckboxButtonGroup;
CheckboxButtonGroup.__name__ = "CheckboxButtonGroup";
CheckboxButtonGroup.init_CheckboxButtonGroup();
