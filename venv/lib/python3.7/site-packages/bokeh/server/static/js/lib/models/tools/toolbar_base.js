"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const logging_1 = require("../../core/logging");
const dom_1 = require("../../core/dom");
const build_views_1 = require("../../core/build_views");
const p = require("../../core/properties");
const dom_view_1 = require("../../core/dom_view");
const array_1 = require("../../core/util/array");
const data_structures_1 = require("../../core/util/data_structures");
const types_1 = require("../../core/util/types");
const model_1 = require("../../model");
const gesture_tool_1 = require("./gestures/gesture_tool");
const action_tool_1 = require("./actions/action_tool");
const help_tool_1 = require("./actions/help_tool");
const inspect_tool_1 = require("./inspectors/inspect_tool");
const toolbar_1 = require("../../styles/toolbar");
const logo_1 = require("../../styles/logo");
const mixins_1 = require("../../styles/mixins");
class ToolbarViewModel extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_ToolbarViewModel() {
        this.define({
            _visible: [p.Any, null],
            autohide: [p.Boolean, false],
        });
    }
    get visible() {
        return (!this.autohide) ? true : (this._visible == null) ? false : this._visible;
    }
}
exports.ToolbarViewModel = ToolbarViewModel;
ToolbarViewModel.__name__ = "ToolbarViewModel";
ToolbarViewModel.init_ToolbarViewModel();
class ToolbarBaseView extends dom_view_1.DOMView {
    initialize() {
        super.initialize();
        this._tool_button_views = {};
        this._build_tool_button_views();
        this._toolbar_view_model = new ToolbarViewModel({ autohide: this.model.autohide });
    }
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.tools.change, () => {
            this._build_tool_button_views();
            this.render();
        });
        this.connect(this.model.properties.autohide.change, () => {
            this._toolbar_view_model.autohide = this.model.autohide;
            this._on_visible_change();
        });
        this.connect(this._toolbar_view_model.properties._visible.change, () => this._on_visible_change());
    }
    remove() {
        build_views_1.remove_views(this._tool_button_views);
        super.remove();
    }
    _build_tool_button_views() {
        const tools = (this.model._proxied_tools != null ? this.model._proxied_tools : this.model.tools); // XXX
        build_views_1.build_views(this._tool_button_views, tools, { parent: this }, (tool) => tool.button_view);
    }
    set_visibility(visible) {
        if (visible != this._toolbar_view_model._visible) {
            this._toolbar_view_model._visible = visible;
        }
    }
    _on_visible_change() {
        const visible = this._toolbar_view_model.visible;
        const hidden_class = toolbar_1.bk_toolbar_hidden;
        if (this.el.classList.contains(hidden_class) && visible) {
            this.el.classList.remove(hidden_class);
        }
        else if (!visible) {
            this.el.classList.add(hidden_class);
        }
    }
    render() {
        dom_1.empty(this.el);
        this.el.classList.add(toolbar_1.bk_toolbar);
        this.el.classList.add(mixins_1.bk_side(this.model.toolbar_location));
        this._toolbar_view_model.autohide = this.model.autohide;
        this._on_visible_change();
        if (this.model.logo != null) {
            const gray = this.model.logo === "grey" ? logo_1.bk_grey : null;
            const logo = dom_1.a({ href: "https://bokeh.org/", target: "_blank", class: [logo_1.bk_logo, logo_1.bk_logo_small, gray] });
            this.el.appendChild(logo);
        }
        const bars = [];
        const el = (tool) => {
            return this._tool_button_views[tool.id].el;
        };
        const { gestures } = this.model;
        for (const et in gestures) {
            bars.push(gestures[et].tools.map(el));
        }
        bars.push(this.model.actions.map(el));
        bars.push(this.model.inspectors.filter((tool) => tool.toggleable).map(el));
        bars.push(this.model.help.map(el));
        for (const bar of bars) {
            if (bar.length !== 0) {
                const el = dom_1.div({ class: toolbar_1.bk_button_bar }, bar);
                this.el.appendChild(el);
            }
        }
    }
    update_layout() { }
    update_position() { }
    after_layout() {
        this._has_finished = true;
    }
}
exports.ToolbarBaseView = ToolbarBaseView;
ToolbarBaseView.__name__ = "ToolbarBaseView";
function createGestureMap() {
    return {
        pan: { tools: [], active: null },
        scroll: { tools: [], active: null },
        pinch: { tools: [], active: null },
        tap: { tools: [], active: null },
        doubletap: { tools: [], active: null },
        press: { tools: [], active: null },
        pressup: { tools: [], active: null },
        rotate: { tools: [], active: null },
        move: { tools: [], active: null },
        multi: { tools: [], active: null },
    };
}
class ToolbarBase extends model_1.Model {
    constructor(attrs) {
        super(attrs);
    }
    static init_ToolbarBase() {
        this.prototype.default_view = ToolbarBaseView;
        this.define({
            tools: [p.Array, []],
            logo: [p.Logo, 'normal'],
            autohide: [p.Boolean, false],
        });
        this.internal({
            gestures: [p.Any, createGestureMap],
            actions: [p.Array, []],
            inspectors: [p.Array, []],
            help: [p.Array, []],
            toolbar_location: [p.Location, 'right'],
        });
    }
    initialize() {
        super.initialize();
        this._init_tools();
    }
    _init_tools() {
        // The only purpose of this function is to avoid unnecessary property churning.
        const tools_changed = function (old_tools, new_tools) {
            if (old_tools.length != new_tools.length) {
                return true;
            }
            const new_ids = new data_structures_1.Set(new_tools.map(t => t.id));
            return array_1.some(old_tools, t => !new_ids.has(t.id));
        };
        const new_inspectors = this.tools.filter(t => t instanceof inspect_tool_1.InspectTool);
        if (tools_changed(this.inspectors, new_inspectors)) {
            this.inspectors = new_inspectors;
        }
        const new_help = this.tools.filter(t => t instanceof help_tool_1.HelpTool);
        if (tools_changed(this.help, new_help)) {
            this.help = new_help;
        }
        const new_actions = this.tools.filter(t => t instanceof action_tool_1.ActionTool);
        if (tools_changed(this.actions, new_actions)) {
            this.actions = new_actions;
        }
        const check_event_type = (et, tool) => {
            if (!(et in this.gestures)) {
                logging_1.logger.warn(`Toolbar: unknown event type '${et}' for tool: ${tool.type} (${tool.id})`);
            }
        };
        const new_gestures = createGestureMap();
        for (const tool of this.tools) {
            if (tool instanceof gesture_tool_1.GestureTool && tool.event_type) {
                if (types_1.isString(tool.event_type)) {
                    new_gestures[tool.event_type].tools.push(tool);
                    check_event_type(tool.event_type, tool);
                }
                else {
                    new_gestures.multi.tools.push(tool);
                    for (const et of tool.event_type) {
                        check_event_type(et, tool);
                    }
                }
            }
        }
        for (const et of Object.keys(new_gestures)) {
            const gm = this.gestures[et];
            if (tools_changed(gm.tools, new_gestures[et].tools)) {
                gm.tools = new_gestures[et].tools;
            }
            if (gm.active && array_1.every(gm.tools, t => t.id != gm.active.id)) {
                gm.active = null;
            }
        }
    }
    get horizontal() {
        return this.toolbar_location === "above" || this.toolbar_location === "below";
    }
    get vertical() {
        return this.toolbar_location === "left" || this.toolbar_location === "right";
    }
    _active_change(tool) {
        const { event_type } = tool;
        if (event_type == null)
            return;
        const event_types = types_1.isString(event_type) ? [event_type] : event_type;
        for (const et of event_types) {
            if (tool.active) {
                const currently_active_tool = this.gestures[et].active;
                if (currently_active_tool != null && tool != currently_active_tool) {
                    logging_1.logger.debug(`Toolbar: deactivating tool: ${currently_active_tool.type} (${currently_active_tool.id}) for event type '${et}'`);
                    currently_active_tool.active = false;
                }
                this.gestures[et].active = tool;
                logging_1.logger.debug(`Toolbar: activating tool: ${tool.type} (${tool.id}) for event type '${et}'`);
            }
            else
                this.gestures[et].active = null;
        }
    }
}
exports.ToolbarBase = ToolbarBase;
ToolbarBase.__name__ = "ToolbarBase";
ToolbarBase.init_ToolbarBase();
