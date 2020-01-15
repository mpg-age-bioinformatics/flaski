"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const icons_1 = require("../../../styles/icons");
class SaveToolView extends action_tool_1.ActionToolView {
    doit() {
        this.plot_view.save("bokeh_plot");
    }
}
exports.SaveToolView = SaveToolView;
SaveToolView.__name__ = "SaveToolView";
class SaveTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Save";
        this.icon = icons_1.bk_tool_icon_save;
    }
    static init_SaveTool() {
        this.prototype.default_view = SaveToolView;
    }
}
exports.SaveTool = SaveTool;
SaveTool.__name__ = "SaveTool";
SaveTool.init_SaveTool();
