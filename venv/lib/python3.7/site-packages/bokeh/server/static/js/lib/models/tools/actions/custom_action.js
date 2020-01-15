"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const p = require("../../../core/properties");
const toolbar_1 = require("../../../styles/toolbar");
class CustomActionButtonView extends action_tool_1.ActionToolButtonView {
    css_classes() {
        return super.css_classes().concat(toolbar_1.bk_toolbar_button_custom_action);
    }
}
exports.CustomActionButtonView = CustomActionButtonView;
CustomActionButtonView.__name__ = "CustomActionButtonView";
class CustomActionView extends action_tool_1.ActionToolView {
    doit() {
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
}
exports.CustomActionView = CustomActionView;
CustomActionView.__name__ = "CustomActionView";
class CustomAction extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Custom Action";
        this.button_view = CustomActionButtonView;
    }
    static init_CustomAction() {
        this.prototype.default_view = CustomActionView;
        this.define({
            action_tooltip: [p.String, 'Perform a Custom Action'],
            callback: [p.Any],
            icon: [p.String],
        });
    }
    get tooltip() {
        return this.action_tooltip;
    }
}
exports.CustomAction = CustomAction;
CustomAction.__name__ = "CustomAction";
CustomAction.init_CustomAction();
