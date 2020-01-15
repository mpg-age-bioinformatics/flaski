"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const icons_1 = require("../../../styles/icons");
class ResetToolView extends action_tool_1.ActionToolView {
    doit() {
        this.plot_view.reset();
    }
}
exports.ResetToolView = ResetToolView;
ResetToolView.__name__ = "ResetToolView";
class ResetTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Reset";
        this.icon = icons_1.bk_tool_icon_reset;
    }
    static init_ResetTool() {
        this.prototype.default_view = ResetToolView;
    }
}
exports.ResetTool = ResetTool;
ResetTool.__name__ = "ResetTool";
ResetTool.init_ResetTool();
