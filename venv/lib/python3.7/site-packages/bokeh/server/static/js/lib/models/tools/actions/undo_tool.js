"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const icons_1 = require("../../../styles/icons");
class UndoToolView extends action_tool_1.ActionToolView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.plot_view.state_changed, () => this.model.disabled = !this.plot_view.can_undo());
    }
    doit() {
        this.plot_view.undo();
    }
}
exports.UndoToolView = UndoToolView;
UndoToolView.__name__ = "UndoToolView";
class UndoTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Undo";
        this.icon = icons_1.bk_tool_icon_undo;
    }
    static init_UndoTool() {
        this.prototype.default_view = UndoToolView;
        this.override({
            disabled: true,
        });
    }
}
exports.UndoTool = UndoTool;
UndoTool.__name__ = "UndoTool";
UndoTool.init_UndoTool();
