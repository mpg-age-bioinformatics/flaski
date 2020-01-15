"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_group_1 = require("./button_group");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const mixins_1 = require("../../styles/mixins");
class RadioButtonGroupView extends button_group_1.ButtonGroupView {
    change_active(i) {
        if (this.model.active !== i) {
            this.model.active = i;
            if (this.model.callback != null)
                this.model.callback.execute(this.model);
        }
    }
    _update_active() {
        const { active } = this.model;
        this._buttons.forEach((button, i) => {
            dom_1.classes(button).toggle(mixins_1.bk_active, active === i);
        });
    }
}
exports.RadioButtonGroupView = RadioButtonGroupView;
RadioButtonGroupView.__name__ = "RadioButtonGroupView";
class RadioButtonGroup extends button_group_1.ButtonGroup {
    constructor(attrs) {
        super(attrs);
    }
    static init_RadioButtonGroup() {
        this.prototype.default_view = RadioButtonGroupView;
        this.define({
            active: [p.Any, null],
        });
    }
}
exports.RadioButtonGroup = RadioButtonGroup;
RadioButtonGroup.__name__ = "RadioButtonGroup";
RadioButtonGroup.init_RadioButtonGroup();
