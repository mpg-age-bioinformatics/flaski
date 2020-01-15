"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_tool_1 = require("../button_tool");
const on_off_button_1 = require("../on_off_button");
const p = require("../../../core/properties");
class InspectToolView extends button_tool_1.ButtonToolView {
}
exports.InspectToolView = InspectToolView;
InspectToolView.__name__ = "InspectToolView";
class InspectTool extends button_tool_1.ButtonTool {
    constructor(attrs) {
        super(attrs);
        this.event_type = "move";
    }
    static init_InspectTool() {
        this.prototype.button_view = on_off_button_1.OnOffButtonView;
        this.define({
            toggleable: [p.Boolean, true],
        });
        this.override({
            active: true,
        });
    }
}
exports.InspectTool = InspectTool;
InspectTool.__name__ = "InspectTool";
InspectTool.init_InspectTool();
