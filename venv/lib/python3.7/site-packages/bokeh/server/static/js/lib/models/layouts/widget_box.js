"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const column_1 = require("./column");
class WidgetBoxView extends column_1.ColumnView {
}
exports.WidgetBoxView = WidgetBoxView;
WidgetBoxView.__name__ = "WidgetBoxView";
class WidgetBox extends column_1.Column {
    constructor(attrs) {
        super(attrs);
    }
    static init_WidgetBox() {
        this.prototype.default_view = WidgetBoxView;
    }
}
exports.WidgetBox = WidgetBox;
WidgetBox.__name__ = "WidgetBox";
WidgetBox.init_WidgetBox();
