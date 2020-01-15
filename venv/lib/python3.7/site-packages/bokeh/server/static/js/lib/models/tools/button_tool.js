"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const dom_view_1 = require("../../core/dom_view");
const tool_1 = require("./tool");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const string_1 = require("../../core/util/string");
const types_1 = require("../../core/util/types");
const toolbar_1 = require("../../styles/toolbar");
class ButtonToolButtonView extends dom_view_1.DOMView {
    initialize() {
        super.initialize();
        this.connect(this.model.change, () => this.render());
        this.el.addEventListener("click", () => this._clicked());
        this.render(); // XXX: this isn't governed by layout, for now
    }
    css_classes() {
        return super.css_classes().concat(toolbar_1.bk_toolbar_button);
    }
    render() {
        dom_1.empty(this.el);
        const icon = this.model.computed_icon;
        if (types_1.isString(icon)) {
            if (string_1.startsWith(icon, "data:image"))
                this.el.style.backgroundImage = "url('" + icon + "')";
            else
                this.el.classList.add(icon);
        }
        this.el.title = this.model.tooltip;
    }
}
exports.ButtonToolButtonView = ButtonToolButtonView;
ButtonToolButtonView.__name__ = "ButtonToolButtonView";
class ButtonToolView extends tool_1.ToolView {
}
exports.ButtonToolView = ButtonToolView;
ButtonToolView.__name__ = "ButtonToolView";
class ButtonTool extends tool_1.Tool {
    constructor(attrs) {
        super(attrs);
    }
    static init_ButtonTool() {
        this.internal({
            disabled: [p.Boolean, false],
        });
    }
    get tooltip() {
        return this.tool_name;
    }
    get computed_icon() {
        return this.icon;
    }
}
exports.ButtonTool = ButtonTool;
ButtonTool.__name__ = "ButtonTool";
ButtonTool.init_ButtonTool();
