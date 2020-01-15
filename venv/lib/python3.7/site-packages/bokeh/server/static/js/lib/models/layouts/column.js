"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const box_1 = require("./box");
const grid_1 = require("../../core/layout/grid");
const p = require("../../core/properties");
class ColumnView extends box_1.BoxView {
    _update_layout() {
        const items = this.child_views.map((child) => child.layout);
        this.layout = new grid_1.Column(items);
        this.layout.rows = this.model.rows;
        this.layout.spacing = [this.model.spacing, 0];
        this.layout.set_sizing(this.box_sizing());
    }
}
exports.ColumnView = ColumnView;
ColumnView.__name__ = "ColumnView";
class Column extends box_1.Box {
    constructor(attrs) {
        super(attrs);
    }
    static init_Column() {
        this.prototype.default_view = ColumnView;
        this.define({
            rows: [p.Any, "auto"],
        });
    }
}
exports.Column = Column;
Column.__name__ = "Column";
Column.init_Column();
