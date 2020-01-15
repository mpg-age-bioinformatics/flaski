"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const control_1 = require("./control");
const dom_1 = require("../../core/dom");
const p = require("../../core/properties");
const inputs_1 = require("../../styles/widgets/inputs");
class InputWidgetView extends control_1.ControlView {
    connect_signals() {
        super.connect_signals();
        this.connect(this.model.properties.title.change, () => {
            this.label_el.textContent = this.model.title;
        });
    }
    render() {
        super.render();
        const { title } = this.model;
        this.label_el = dom_1.label({ style: { display: title.length == 0 ? "none" : "" } }, title);
        this.group_el = dom_1.div({ class: inputs_1.bk_input_group }, this.label_el);
        this.el.appendChild(this.group_el);
    }
    change_input() {
        if (this.model.callback != null)
            this.model.callback.execute(this.model);
    }
}
exports.InputWidgetView = InputWidgetView;
InputWidgetView.__name__ = "InputWidgetView";
class InputWidget extends control_1.Control {
    constructor(attrs) {
        super(attrs);
    }
    static init_InputWidget() {
        this.define({
            title: [p.String, ""],
            callback: [p.Any],
        });
    }
}
exports.InputWidget = InputWidget;
InputWidget.__name__ = "InputWidget";
InputWidget.init_InputWidget();
