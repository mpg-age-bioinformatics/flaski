"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const button_tool_1 = require("../button_tool");
const on_off_button_1 = require("../on_off_button");
class GestureToolView extends button_tool_1.ButtonToolView {
}
exports.GestureToolView = GestureToolView;
GestureToolView.__name__ = "GestureToolView";
class GestureTool extends button_tool_1.ButtonTool {
    constructor(attrs) {
        super(attrs);
        this.button_view = on_off_button_1.OnOffButtonView;
    }
}
exports.GestureTool = GestureTool;
GestureTool.__name__ = "GestureTool";
