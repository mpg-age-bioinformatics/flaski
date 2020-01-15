"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const box_1 = require("./box");
const grid_1 = require("../../core/layout/grid");
const p = require("../../core/properties");
class RowView extends box_1.BoxView {
    _update_layout() {
        const items = this.child_views.map((child) => child.layout);
        this.layout = new grid_1.Row(items);
        this.layout.cols = this.model.cols;
        this.layout.spacing = [0, this.model.spacing];
        this.layout.set_sizing(this.box_sizing());
    }
}
exports.RowView = RowView;
RowView.__name__ = "RowView";
class Row extends box_1.Box {
    constructor(attrs) {
        super(attrs);
    }
    static init_Row() {
        this.prototype.default_view = RowView;
        this.define({
            cols: [p.Any, "auto"],
        });
    }
}
exports.Row = Row;
Row.__name__ = "Row";
Row.init_Row();
