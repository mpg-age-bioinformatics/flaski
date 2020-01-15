"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_tool_1 = require("../button_tool");
const signaling_1 = require("../../../core/signaling");
class ActionToolButtonView extends button_tool_1.ButtonToolButtonView {
    _clicked() {
        this.model.do.emit();
    }
}
exports.ActionToolButtonView = ActionToolButtonView;
ActionToolButtonView.__name__ = "ActionToolButtonView";
class ActionToolView extends button_tool_1.ButtonToolView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.do, () => this.doit());
    }
}
exports.ActionToolView = ActionToolView;
ActionToolView.__name__ = "ActionToolView";
class ActionTool extends button_tool_1.ButtonTool {
    constructor(attrs) {
        super(attrs);
        this.button_view = ActionToolButtonView;
        this.do = new signaling_1.Signal0(this, "do");
    }
}
exports.ActionTool = ActionTool;
ActionTool.__name__ = "ActionTool";
