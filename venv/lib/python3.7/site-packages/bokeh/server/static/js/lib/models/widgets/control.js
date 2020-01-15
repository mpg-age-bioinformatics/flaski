"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const widget_1 = require("./widget");
class ControlView extends widget_1.WidgetView {
    connect_signals() {
        super.connect_signals();
        const p = this.model.properties;
        this.on_change(p.disabled, () => this.render());
    }
}
exports.ControlView = ControlView;
ControlView.__name__ = "ControlView";
class Control extends widget_1.Widget {
    constructor(attrs) {
        super(attrs);
    }
}
exports.Control = Control;
Control.__name__ = "Control";
