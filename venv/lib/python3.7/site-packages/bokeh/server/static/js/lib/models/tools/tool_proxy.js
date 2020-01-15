"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const signaling_1 = require("../../core/signaling");
const model_1 = require("../../model");
const inspect_tool_1 = require("./inspectors/inspect_tool");
class ToolProxy extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_ToolProxy() {
        this.define({
            tools: [p.Array, []],
            active: [p.Boolean, false],
            disabled: [p.Boolean, false],
        });
    }
    // Operates all the tools given only one button
    get button_view() {
        return this.tools[0].button_view;
    }
    get event_type() {
        return this.tools[0].event_type;
    }
    get tooltip() {
        return this.tools[0].tooltip;
    }
    get tool_name() {
        return this.tools[0].tool_name;
    }
    get icon() {
        return this.tools[0].computed_icon;
    }
    get computed_icon() {
        return this.icon;
    }
    get toggleable() {
        const tool = this.tools[0];
        return tool instanceof inspect_tool_1.InspectTool && tool.toggleable;
    }
    initialize() {
        super.initialize();
        this.do = new signaling_1.Signal0(this, "do");
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.do, () => this.doit());
        this.connect(this.properties.active.change, () => this.set_active());
    }
    doit() {
        for (const tool of this.tools) {
            tool.do.emit();
        }
    }
    set_active() {
        for (const tool of this.tools) {
            tool.active = this.active;
        }
    }
}
exports.ToolProxy = ToolProxy;
ToolProxy.__name__ = "ToolProxy";
ToolProxy.init_ToolProxy();
