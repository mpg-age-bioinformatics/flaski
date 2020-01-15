"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const action_tool_1 = require("./action_tool");
const p = require("../../../core/properties");
const icons_1 = require("../../../styles/icons");
class HelpToolView extends action_tool_1.ActionToolView {
    doit() {
        window.open(this.model.redirect);
    }
}
exports.HelpToolView = HelpToolView;
HelpToolView.__name__ = "HelpToolView";
class HelpTool extends action_tool_1.ActionTool {
    constructor(attrs) {
        super(attrs);
        this.tool_name = "Help";
        this.icon = icons_1.bk_tool_icon_help;
    }
    static init_HelpTool() {
        this.prototype.default_view = HelpToolView;
        this.define({
            help_tooltip: [p.String, 'Click the question mark to learn more about Bokeh plot tools.'],
            redirect: [p.String, 'https://docs.bokeh.org/en/latest/docs/user_guide/tools.html'],
        });
    }
    get tooltip() {
        return this.help_tooltip;
    }
}
exports.HelpTool = HelpTool;
HelpTool.__name__ = "HelpTool";
HelpTool.init_HelpTool();
