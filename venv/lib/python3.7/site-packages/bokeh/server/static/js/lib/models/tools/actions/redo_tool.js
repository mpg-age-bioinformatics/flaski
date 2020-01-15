"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const icons_1 = require("../../../styles/icons");
class RedoToolView extends action_tool_1.ActionToolView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.plot_view.state_changed, () => this.model.disabled = !this.plot_view.can_redo());
    }
    doit() {
        this.plot_view.redo();
    }
}
exports.RedoToolView = RedoToolView;
RedoToolView.__name__ = "RedoToolView";
class RedoTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Redo";
        this.icon = icons_1.bk_tool_icon_redo;
    }
    static init_RedoTool() {
        this.prototype.default_view = RedoToolView;
        this.override({
            disabled: true,
        });
    }
}
exports.RedoTool = RedoTool;
RedoTool.__name__ = "RedoTool";
RedoTool.init_RedoTool();
