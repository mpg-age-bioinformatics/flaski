"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const p = require("../../core/properties");
const array_1 = require("../../core/util/array");
const toolbar_base_1 = require("./toolbar_base");
const tool_proxy_1 = require("./tool_proxy");
const layout_dom_1 = require("../layouts/layout_dom");
const layout_1 = require("../../core/layout");
class ProxyToolbar extends toolbar_base_1.ToolbarBase {
    constructor(attrs) {
        super(attrs);
    }
    initialize() {
        super.initialize();
        this._merge_tools();
    }
    _merge_tools() {
        // Go through all the tools on the toolbar and replace them with
        // a proxy e.g. PanTool, BoxSelectTool, etc.
        this._proxied_tools = [];
        const inspectors = {};
        const actions = {};
        const gestures = {};
        const new_help_tools = [];
        const new_help_urls = [];
        for (const helptool of this.help) {
            if (!array_1.includes(new_help_urls, helptool.redirect)) {
                new_help_tools.push(helptool);
                new_help_urls.push(helptool.redirect);
            }
        }
        this._proxied_tools.push(...new_help_tools);
        this.help = new_help_tools;
        for (const event_type in this.gestures) {
            const gesture = this.gestures[event_type];
            if (!(event_type in gestures)) {
                gestures[event_type] = {};
            }
            for (const tool of gesture.tools) {
                if (!(tool.type in gestures[event_type])) {
                    gestures[event_type][tool.type] = [];
                }
                gestures[event_type][tool.type].push(tool);
            }
        }
        for (const tool of this.inspectors) {
            if (!(tool.type in inspectors)) {
                inspectors[tool.type] = [];
            }
            inspectors[tool.type].push(tool);
        }
        for (const tool of this.actions) {
            if (!(tool.type in actions)) {
                actions[tool.type] = [];
            }
            actions[tool.type].push(tool);
        }
        // Add a proxy for each of the groups of tools.
        const make_proxy = (tools, active = false) => {
            const proxy = new tool_proxy_1.ToolProxy({ tools, active });
            this._proxied_tools.push(proxy);
            return proxy;
        };
        for (const event_type in gestures) {
            const gesture = this.gestures[event_type];
            gesture.tools = [];
            for (const tool_type in gestures[event_type]) {
                const tools = gestures[event_type][tool_type];
                if (tools.length > 0) {
                    if (event_type == 'multi') {
                        for (const tool of tools) {
                            const proxy = make_proxy([tool]);
                            gesture.tools.push(proxy);
                            this.connect(proxy.properties.active.change, this._active_change.bind(this, proxy));
                        }
                    }
                    else {
                        const proxy = make_proxy(tools);
                        gesture.tools.push(proxy);
                        this.connect(proxy.properties.active.change, this._active_change.bind(this, proxy));
                    }
                }
            }
        }
        this.actions = [];
        for (const tool_type in actions) {
            const tools = actions[tool_type];
            if (tool_type == 'CustomAction') {
                for (const tool of tools)
                    this.actions.push(make_proxy([tool]));
            }
            else if (tools.length > 0) {
                this.actions.push(make_proxy(tools)); // XXX
            }
        }
        this.inspectors = [];
        for (const tool_type in inspectors) {
            const tools = inspectors[tool_type];
            if (tools.length > 0)
                this.inspectors.push(make_proxy(tools, true)); // XXX
        }
        for (const et in this.gestures) {
            const gesture = this.gestures[et];
            if (gesture.tools.length == 0)
                continue;
            gesture.tools = array_1.sort_by(gesture.tools, (tool) => tool.default_order);
            if (!(et == 'pinch' || et == 'scroll' || et == 'multi'))
                gesture.tools[0].active = true;
        }
    }
}
exports.ProxyToolbar = ProxyToolbar;
ProxyToolbar.__name__ = "ProxyToolbar";
class ToolbarBoxView extends layout_dom_1.LayoutDOMView {
    initialize() {
        this.model.toolbar.toolbar_location = this.model.toolbar_location;
        super.initialize();
    }
    get child_models() {
        return [this.model.toolbar]; // XXX
    }
    _update_layout() {
        this.layout = new layout_1.ContentBox(this.child_views[0].el);
        const { toolbar } = this.model;
        if (toolbar.horizontal) {
            this.layout.set_sizing({
                width_policy: "fit", min_width: 100, height_policy: "fixed",
            });
        }
        else {
            this.layout.set_sizing({
                width_policy: "fixed", height_policy: "fit", min_height: 100,
            });
        }
    }
}
exports.ToolbarBoxView = ToolbarBoxView;
ToolbarBoxView.__name__ = "ToolbarBoxView";
class ToolbarBox extends layout_dom_1.LayoutDOM {
    constructor(attrs) {
        super(attrs);
    }
    static init_ToolbarBox() {
        this.prototype.default_view = ToolbarBoxView;
        this.define({
            toolbar: [p.Instance],
            toolbar_location: [p.Location, "right"],
        });
    }
}
exports.ToolbarBox = ToolbarBox;
ToolbarBox.__name__ = "ToolbarBox";
ToolbarBox.init_ToolbarBox();
