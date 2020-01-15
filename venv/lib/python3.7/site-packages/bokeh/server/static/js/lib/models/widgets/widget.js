"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const html_box_1 = require("../layouts/html_box");
const p = require("../../core/properties");
class WidgetView extends html_box_1.HTMLBoxView {
    _width_policy() {
        return this.model.orientation == "horizontal" ? super._width_policy() : "fixed";
    }
    _height_policy() {
        return this.model.orientation == "horizontal" ? "fixed" : super._height_policy();
    }
    box_sizing() {
        const sizing = super.box_sizing();
        if (this.model.orientation == "horizontal") {
            if (sizing.width == null)
                sizing.width = this.model.default_size;
        }
        else {
            if (sizing.height == null)
                sizing.height = this.model.default_size;
        }
        return sizing;
    }
}
exports.WidgetView = WidgetView;
WidgetView.__name__ = "WidgetView";
class Widget extends html_box_1.HTMLBox {
    constructor(attrs) {
        super(attrs);
    }
    static init_Widget() {
        this.define({
            orientation: [p.Orientation, "horizontal"],
            default_size: [p.Number, 300],
        });
        this.override({
            margin: [5, 5, 5, 5],
        });
    }
}
exports.Widget = Widget;
Widget.__name__ = "Widget";
Widget.init_Widget();
