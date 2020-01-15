"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const types_1 = require("../../core/util/types");
const array_1 = require("../../core/util/array");
const inspect_tool_1 = require("./inspectors/inspect_tool");
const toolbar_base_1 = require("./toolbar_base");
const _get_active_attr = (et) => {
    switch (et) {
        case 'tap': return 'active_tap';
        case 'pan': return 'active_drag';
        case 'pinch':
        case 'scroll': return 'active_scroll';
        case 'multi': return 'active_multi';
    }
    return null;
};
const _supports_auto = (et) => {
    return et == 'tap' || et == 'pan';
};
class Toolbar extends toolbar_base_1.ToolbarBase {
    constructor(attrs) {
        super(attrs);
    }
    static init_Toolbar() {
        this.prototype.default_view = toolbar_base_1.ToolbarBaseView;
        this.define({
            active_drag: [p.Any, 'auto'],
            active_inspect: [p.Any, 'auto'],
            active_scroll: [p.Any, 'auto'],
            active_tap: [p.Any, 'auto'],
            active_multi: [p.Any, null],
        });
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.properties.tools.change, () => this._init_tools());
    }
    _init_tools() {
        super._init_tools();
        if (this.active_inspect == 'auto') {
            // do nothing as all tools are active be default
        }
        else if (this.active_inspect instanceof inspect_tool_1.InspectTool) {
            let found = false;
            for (const inspector of this.inspectors) {
                if (inspector != this.active_inspect)
                    inspector.active = false;
                else
                    found = true;
            }
            if (!found) {
                this.active_inspect = null;
            }
        }
        else if (types_1.isArray(this.active_inspect)) {
            const active_inspect = array_1.intersection(this.active_inspect, this.inspectors);
            if (active_inspect.length != this.active_inspect.length) {
                this.active_inspect = active_inspect;
            }
            for (const inspector of this.inspectors) {
                if (!array_1.includes(this.active_inspect, inspector))
                    inspector.active = false;
            }
        }
        else if (this.active_inspect == null) {
            for (const inspector of this.inspectors)
                inspector.active = false;
        }
        const _activate_gesture = (tool) => {
            if (tool.active) {
                // tool was activated by a proxy, but we need to finish configuration manually
                this._active_change(tool);
            }
            else
                tool.active = true;
        };
        // Connecting signals has to be done before changing the active state of the tools.
        for (const et in this.gestures) {
            const gesture = this.gestures[et];
            gesture.tools = array_1.sort_by(gesture.tools, (tool) => tool.default_order);
            for (const tool of gesture.tools) {
                this.connect(tool.properties.active.change, this._active_change.bind(this, tool));
            }
        }
        for (const et in this.gestures) {
            const active_attr = _get_active_attr(et);
            if (active_attr) {
                const active_tool = this[active_attr];
                if (active_tool == 'auto') {
                    const gesture = this.gestures[et];
                    if (gesture.tools.length != 0 && _supports_auto(et)) {
                        _activate_gesture(gesture.tools[0]);
                    }
                }
                else if (active_tool != null) {
                    if (array_1.includes(this.tools, active_tool)) {
                        _activate_gesture(active_tool);
                    }
                    else {
                        this[active_attr] = null;
                    }
                }
            }
        }
    }
}
exports.Toolbar = Toolbar;
Toolbar.__name__ = "Toolbar";
Toolbar.init_Toolbar();
